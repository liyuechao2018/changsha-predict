from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class PredictionRequest:
    year: int
    score: float
    quality_level: str
    rank: Optional[int] = None


class PredictionService:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def predict(self, request: PredictionRequest) -> dict:
        if request.rank is None or request.rank <= 0:
            raise ValueError("请填写有效位次。")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            config = self._get_year_config(conn, request.year)
            rank = request.rank
            rank_source = "用户填写位次"
            rows = self._get_admissions(conn, config["admission_data_year"])
            structure_changes = self._get_structure_changes(conn, request.year)

        school_items = self._build_school_items(
            rows,
            rank,
            structure_changes,
            config["admission_data_year"],
        )
        limited_groups, landing_school = self._recommend_by_rank_sequence(school_items, rank)
        return {
            "student": {
                "year": request.year,
                "score": request.score,
                "qualityLevel": request.quality_level,
                "rank": rank,
                "rankSource": rank_source,
                "summary": self._summary(limited_groups),
            },
            "landingSchool": landing_school,
            "rule": {
                "name": "排序邻域切片模型",
            },
            "structureChanges": self._summarize_structure_changes(structure_changes),
            "groups": limited_groups,
        }

    def _get_year_config(self, conn: sqlite3.Connection, year: int) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM year_configs WHERE year = ?", (year,)).fetchone()
        if row is None:
            raise ValueError(f"未找到 {year} 年配置。")
        return row

    def _get_admissions(self, conn: sqlite3.Connection, year: int) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT
                ah.school_id,
                s.name AS school_name,
                s.tier,
                s.admission_batch,
                ah.admission_score,
                ah.rank_without_quota,
                ah.enrollment_plan
            FROM admission_history ah
            JOIN schools s ON s.id = ah.school_id
            WHERE ah.year = ? AND s.is_active = 1
            ORDER BY ah.rank_without_quota ASC
            """,
            (year,),
        ).fetchall()

    def _get_structure_changes(self, conn: sqlite3.Connection, year: int) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT *
            FROM structure_changes
            WHERE year = ? AND is_active = 1
            ORDER BY impact_start_rank ASC, effective_seats DESC
            """,
            (year,),
        ).fetchall()

    def _structure_adjustment(self, school_rank: int, school_batch: str, changes: list[sqlite3.Row]) -> tuple[int, list[dict]]:
        total = 0
        items: list[dict] = []
        for change in changes:
            if change["admission_batch"] != school_batch:
                continue
            influence = self._rank_influence(
                school_rank,
                int(change["impact_start_rank"]),
                int(change["impact_full_rank"]),
                int(change["impact_end_rank"]),
            )
            if influence <= 0:
                continue
            impact = round(int(change["effective_seats"]) * float(change["heat_factor"]) * influence)
            if impact <= 0:
                continue
            total += impact
            items.append(
                {
                    "schoolName": change["school_name"],
                    "changeType": change["change_type"],
                    "admissionBatch": change["admission_batch"],
                    "impact": impact,
                    "benchmark": change["benchmark"],
                }
            )
        return total, items

    def _build_school_items(
        self,
        rows: list[sqlite3.Row],
        student_rank: int,
        structure_changes: list[sqlite3.Row],
        year: int,
    ) -> list[dict]:
        items = []
        for row in rows:
            original_rank = int(row["rank_without_quota"])
            adjustment, adjustment_items = self._structure_adjustment(
                original_rank,
                row["admission_batch"],
                structure_changes,
            )
            adjusted_rank = original_rank + adjustment
            gap = student_rank - adjusted_rank
            items.append(
                {
                    "schoolId": row["school_id"],
                    "schoolName": row["school_name"],
                    "category": "",
                    "probability": 0,
                    "admissionScore": row["admission_score"],
                    "admissionRank": original_rank,
                    "adjustedAdmissionRank": adjusted_rank,
                    "structureAdjustment": adjustment,
                    "structureAdjustmentItems": adjustment_items,
                    "rankGap": gap,
                    "enrollmentPlan": row["enrollment_plan"],
                    "tier": row["tier"],
                    "admissionBatch": row["admission_batch"],
                    "stars": 0,
                    "reason": "",
                    "referenceYear": year,
                }
            )

        return sorted(
            items,
            key=lambda item: (item["adjustedAdmissionRank"], item["admissionRank"], item["schoolId"]),
        )

    def _recommend_by_rank_sequence(self, school_items: list[dict], student_rank: int) -> tuple[dict[str, list[dict]], dict]:
        if not school_items:
            return {"reach": [], "target": [], "safety": []}, {}

        nearest_index = min(
            range(len(school_items)),
            key=lambda index: (
                abs(student_rank - school_items[index]["adjustedAdmissionRank"]),
                school_items[index]["adjustedAdmissionRank"],
            ),
        )

        if student_rank <= 2000:
            return self._recommend_for_top_rank(school_items, student_rank, nearest_index)

        total = min(10, len(school_items))
        counts = self._group_counts(total)
        reach_count = counts["reach"]
        target_count = counts["target"]
        safety_count = counts["safety"]

        # Normal case: anchor has three stronger schools before it, so it starts target.
        # Edges are clamped into a contiguous, duplicate-free window and then sliced.
        window_start = nearest_index - reach_count
        window_start = min(max(window_start, 0), len(school_items) - total)
        window = school_items[window_start : window_start + total]
        selected = {
            "reach": window[:reach_count],
            "target": window[reach_count : reach_count + target_count],
            "safety": window[reach_count + target_count : reach_count + target_count + safety_count],
        }

        for category, schools in selected.items():
            for school in schools:
                school["category"] = self._category_label(category)
                school["probability"] = self._sequence_probability(category, school["rankGap"])
                school["stars"] = self._stars(school["probability"])
                school["reason"] = self._sequence_reason(
                    category,
                    student_rank,
                    school["schoolName"],
                    school["admissionRank"],
                    school["adjustedAdmissionRank"],
                    school["rankGap"],
                    school["structureAdjustment"],
                    school["referenceYear"],
                )

        landing_school = {
            "schoolId": school_items[nearest_index]["schoolId"],
            "schoolName": school_items[nearest_index]["schoolName"],
            "adjustedAdmissionRank": school_items[nearest_index]["adjustedAdmissionRank"],
            "rankGap": school_items[nearest_index]["rankGap"],
        }
        return selected, landing_school

    def _recommend_for_top_rank(
        self,
        school_items: list[dict],
        student_rank: int,
        nearest_index: int,
    ) -> tuple[dict[str, list[dict]], dict]:
        reach = school_items[:nearest_index]
        target_end = min(max(nearest_index + 4, 4), len(school_items))
        target = school_items[nearest_index:target_end]
        safety = school_items[target_end : min(target_end + 2, len(school_items))]
        selected = {"reach": reach[:3], "target": target, "safety": safety}

        for category, schools in selected.items():
            for school in schools:
                school["category"] = self._category_label(category)
                school["probability"] = self._sequence_probability(category, school["rankGap"])
                school["stars"] = self._stars(school["probability"])
                school["reason"] = self._sequence_reason(
                    category,
                    student_rank,
                    school["schoolName"],
                    school["admissionRank"],
                    school["adjustedAdmissionRank"],
                    school["rankGap"],
                    school["structureAdjustment"],
                    school["referenceYear"],
                )

        landing_school = {
            "schoolId": school_items[nearest_index]["schoolId"],
            "schoolName": school_items[nearest_index]["schoolName"],
            "adjustedAdmissionRank": school_items[nearest_index]["adjustedAdmissionRank"],
            "rankGap": school_items[nearest_index]["rankGap"],
        }
        return selected, landing_school

    def _group_counts(self, total: int) -> dict[str, int]:
        if total >= 10:
            return {"reach": 3, "target": 4, "safety": 3}
        if total <= 0:
            return {"reach": 0, "target": 0, "safety": 0}
        if total == 1:
            return {"reach": 0, "target": 1, "safety": 0}
        if total == 2:
            return {"reach": 1, "target": 1, "safety": 0}
        if total == 3:
            return {"reach": 1, "target": 1, "safety": 1}
        if total == 4:
            return {"reach": 1, "target": 2, "safety": 1}
        if total == 5:
            return {"reach": 1, "target": 2, "safety": 2}
        if total == 6:
            return {"reach": 2, "target": 2, "safety": 2}
        if total == 7:
            return {"reach": 2, "target": 3, "safety": 2}
        if total == 8:
            return {"reach": 3, "target": 3, "safety": 2}
        return {"reach": 3, "target": 4, "safety": 2}

    def _rank_influence(self, rank: int, start: int, full: int, end: int) -> float:
        if rank < start:
            return 0.0
        if rank < full:
            return (rank - start) / max(1, full - start)
        if rank <= end:
            return 1.0
        # Past the main parent-choice range, the effect should still exist but fade.
        tail = max(1, end - full)
        fade = max(0.0, 1.0 - ((rank - end) / tail))
        return 0.35 * fade

    def _sequence_probability(self, category: str, gap: int) -> int:
        distance = min(abs(gap), 3000)
        if category == "reach":
            return max(35, round(62 - distance / 3000 * 18))
        if category == "target":
            return max(68, round(86 - distance / 3000 * 10))
        return min(96, round(88 + distance / 3000 * 8))

    def _stars(self, probability: int) -> int:
        if probability >= 90:
            return 5
        if probability >= 80:
            return 4
        if probability >= 65:
            return 3
        if probability >= 45:
            return 2
        return 1

    def _sequence_reason(
        self,
        category: str,
        student_rank: int,
        school_name: str,
        school_rank: int,
        adjusted_rank: int,
        gap: int,
        adjustment: int,
        year: int,
    ) -> str:
        adjustment_text = ""
        if adjustment > 0:
            adjustment_text = f"；考虑2026新增/扩建学位后，参考位次约 {adjusted_rank}"
        relation = f"靠后 {gap} 名" if gap > 0 else f"领先 {abs(gap)} 名"
        if gap == 0:
            relation = "基本持平"
        if category == "reach":
            return f"按录取位次序列看，{school_name}位于你的落位学校上方；你的位次约 {student_rank}，{year} 年该校录取位次约 {school_rank}{adjustment_text}，当前{relation}，作为冲刺参考。"
        if category == "target":
            return f"按录取位次序列看，{school_name}接近你的落位区间；你的位次约 {student_rank}，{year} 年该校录取位次约 {school_rank}{adjustment_text}，当前{relation}，作为稳妥参考。"
        return f"按录取位次序列看，{school_name}位于落位区间下方；你的位次约 {student_rank}，{year} 年该校录取位次约 {school_rank}{adjustment_text}，当前{relation}，作为保底参考。"

    def _category_label(self, category: str) -> str:
        return {"reach": "冲", "target": "稳", "safety": "保"}[category]

    def _summary(self, groups: dict[str, list[dict]]) -> str:
        total = sum(len(items) for items in groups.values())
        if total == 10:
            return "已生成 10 所推荐"
        return "暂无匹配推荐"

    def _summarize_structure_changes(self, changes: list[sqlite3.Row]) -> list[dict]:
        return [
            {
                "schoolName": row["school_name"],
                "changeType": row["change_type"],
                "admissionBatch": row["admission_batch"],
                "plannedSeats": row["planned_seats"],
                "effectiveSeats": row["effective_seats"],
                "benchmark": row["benchmark"],
                "heatFactor": row["heat_factor"],
            }
            for row in changes
        ]
