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
        if request.score <= 0:
            raise ValueError("分数必须大于 0。")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            config = self._get_year_config(conn, request.year)
            rule = self._get_rule(conn, request.year)
            rank, rank_source = self._resolve_rank(conn, request, config["admission_data_year"])
            rows = self._get_admissions(conn, config["admission_data_year"])
            structure_changes = self._get_structure_changes(conn, request.year)

        groups = {"reach": [], "target": [], "safety": []}
        for row in rows:
            original_rank = int(row["rank_without_quota"])
            adjustment, adjustment_items = self._structure_adjustment(
                original_rank,
                row["admission_batch"],
                structure_changes,
            )
            adjusted_rank = original_rank + adjustment
            gap = rank - adjusted_rank
            category = self._classify_gap(gap, rule)
            if category is None:
                continue
            probability = self._probability(category, gap, rule)
            groups[category].append(
                {
                    "schoolId": row["school_id"],
                    "schoolName": row["school_name"],
                    "category": self._category_label(category),
                    "probability": probability,
                    "admissionScore": row["admission_score"],
                    "admissionRank": original_rank,
                    "adjustedAdmissionRank": adjusted_rank,
                    "structureAdjustment": adjustment,
                    "structureAdjustmentItems": adjustment_items,
                    "rankGap": gap,
                    "enrollmentPlan": row["enrollment_plan"],
                    "tier": row["tier"],
                    "admissionBatch": row["admission_batch"],
                    "stars": self._stars(probability),
                    "reason": self._reason(
                        category,
                        rank,
                        row["school_name"],
                        original_rank,
                        adjusted_rank,
                        gap,
                        adjustment,
                        config["admission_data_year"],
                    ),
                }
            )

        groups["reach"].sort(key=lambda item: abs(item["rankGap"]))
        groups["target"].sort(key=lambda item: abs(item["rankGap"]))
        groups["safety"].sort(key=lambda item: item["rankGap"], reverse=True)

        limit = int(rule["max_items_per_group"])
        limited_groups = {key: value[:limit] for key, value in groups.items()}
        return {
            "student": {
                "year": request.year,
                "score": request.score,
                "qualityLevel": request.quality_level,
                "rank": rank,
                "rankSource": rank_source,
                "summary": self._summary(limited_groups),
            },
            "rule": {
                "name": rule["name"],
                "reach": f"+{rule['reach_min_gap']} 到 +{rule['reach_max_gap']} 名",
                "target": f"{rule['target_min_gap']} 到 {rule['target_max_gap']} 名",
                "safety": f"小于等于 {rule['safety_max_gap']} 名",
            },
            "structureChanges": self._summarize_structure_changes(structure_changes),
            "groups": limited_groups,
        }

    def _get_year_config(self, conn: sqlite3.Connection, year: int) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM year_configs WHERE year = ?", (year,)).fetchone()
        if row is None:
            raise ValueError(f"未找到 {year} 年配置。")
        return row

    def _get_rule(self, conn: sqlite3.Connection, year: int) -> sqlite3.Row:
        row = conn.execute(
            """
            SELECT * FROM prediction_rules
            WHERE is_active = 1 AND (year = ? OR year IS NULL)
            ORDER BY year DESC
            LIMIT 1
            """,
            (year,),
        ).fetchone()
        if row is None:
            raise ValueError(f"未找到 {year} 年预测规则。")
        return row

    def _resolve_rank(self, conn: sqlite3.Connection, request: PredictionRequest, reference_year: int) -> tuple[int, str]:
        if request.rank is not None:
            return request.rank, "用户填写位次"

        official = conn.execute(
            "SELECT cumulative_count FROM score_rankings WHERE year = ? AND score = ?",
            (request.year, request.score),
        ).fetchone()
        if official is not None:
            return int(official["cumulative_count"]), "当年两分一段表"

        estimated = self._estimate_rank_from_reference(conn, request.score, reference_year)
        return estimated, f"根据 {reference_year} 年录取数据估算"

    def _estimate_rank_from_reference(self, conn: sqlite3.Connection, score: float, reference_year: int) -> int:
        points = conn.execute(
            """
            SELECT admission_score, rank_without_quota
            FROM admission_history
            WHERE year = ?
            ORDER BY admission_score DESC, rank_without_quota ASC
            """,
            (reference_year,),
        ).fetchall()
        if not points:
            raise ValueError("没有可用于估算位次的参考数据。")

        compact: list[tuple[float, int]] = []
        seen = set()
        for point in points:
            score_value = float(point["admission_score"])
            if score_value in seen:
                continue
            compact.append((score_value, int(point["rank_without_quota"])))
            seen.add(score_value)

        if score >= compact[0][0]:
            return compact[0][1]
        if score <= compact[-1][0]:
            return compact[-1][1]

        for left, right in zip(compact, compact[1:]):
            high_score, high_rank = left
            low_score, low_rank = right
            if high_score >= score >= low_score:
                ratio = (high_score - score) / (high_score - low_score)
                return round(high_rank + ratio * (low_rank - high_rank))

        return compact[-1][1]

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

    def _classify_gap(self, gap: int, rule: sqlite3.Row) -> Optional[str]:
        if rule["reach_min_gap"] <= gap <= rule["reach_max_gap"]:
            return "reach"
        if rule["target_min_gap"] <= gap <= rule["target_max_gap"]:
            return "target"
        if gap <= rule["safety_max_gap"]:
            return "safety"
        return None

    def _probability(self, category: str, gap: int, rule: sqlite3.Row) -> int:
        if category == "reach":
            span = max(1, rule["reach_max_gap"] - rule["reach_min_gap"])
            progress = (gap - rule["reach_min_gap"]) / span
            return round(60 - progress * 25)
        if category == "target":
            span = max(1, rule["target_max_gap"] - rule["target_min_gap"])
            progress = (gap - rule["target_min_gap"]) / span
            return round(85 - progress * 10)
        safety_depth = min(abs(gap - rule["safety_max_gap"]), 2000)
        return round(88 + (safety_depth / 2000) * 8)

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

    def _reason(
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
            adjustment_text = f"；考虑2026新增/扩建学位后，参考位次修正为约 {adjusted_rank}"
        if category == "reach":
            return f"你的位次约 {student_rank}，{year} 年{school_name}录取位次约 {school_rank}{adjustment_text}，当前靠后 {gap} 名，属于有机会但存在风险的冲刺选择。"
        if category == "target":
            ahead = abs(gap)
            return f"你的位次约 {student_rank}，{year} 年{school_name}录取位次约 {school_rank}{adjustment_text}，当前领先 {ahead} 名，接近录取线，属于相对稳妥的选择。"
        ahead = abs(gap)
        return f"你的位次约 {student_rank}，明显优于 {year} 年{school_name}录取位次 {school_rank}{adjustment_text}，领先约 {ahead} 名，录取把握较高。"

    def _category_label(self, category: str) -> str:
        return {"reach": "冲", "target": "稳", "safety": "保"}[category]

    def _summary(self, groups: dict[str, list[dict]]) -> str:
        if groups["target"]:
            return "较稳"
        if groups["reach"] and groups["safety"]:
            return "有冲有保"
        if groups["safety"]:
            return "整体稳妥"
        if groups["reach"]:
            return "偏冲刺"
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
