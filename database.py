from __future__ import annotations

import sqlite3
from pathlib import Path


ADMISSIONS_2025 = [
    ("长郡", 658, 981, 2206),
    ("雅礼", 656, 1192, 2883),
    ("师大附中", 654, 1642, 3677),
    ("市一中", 653, 1876, 4076),
    ("雅礼新", 651, 2363, 4926),
    ("麓山国际", 648, 3140, 6418),
    ("师大附中新", 647, 3391, 6935),
    ("市一中新", 646, 3642, 7453),
    ("南雅", 646, 3642, 7453),
    ("明德", 643, 4470, 9073),
    ("周南", 640, 5340, 10723),
    ("市实验", 636, 6881, 13089),
    ("长郡双语", 637, 6481, 12492),
    ("师梅", 636, 6881, 13089),
    ("雅礼洋湖", 636, 6881, 13089),
    ("雅礼实验", 634, 7698, 14234),
    ("长梅", 633, 8153, 14820),
    ("周梅", 632, 8608, 15407),
    ("长郡滨江", 631, 9056, 15973),
    ("市六中", 629, 9953, 17120),
    ("附中博才湘江", 628, 10403, 17701),
    ("长外", 626, 11317, 18824),
    ("望城一中", 625, 11717, 19349),
    ("麓山梅溪湖", 623, 12526, 20394),
    ("麓山滨江", 622, 12936, 20914),
    ("明德华兴", 621, 13311, 21438),
    ("东雅", 618, 14402, 22919),
    ("长郡湘府", 616, 15105, 23895),
    ("长铁一中", 616, 15105, 23895),
    ("周南实验", 615, 15433, 24374),
    ("市十五中", 614, 15761, 24854),
    ("市十一中城南路", 612, 16390, 25759),
    ("南雅梅溪湖", 612, 16391, 25760),
    ("地质", 611, 16706, 26217),
    ("雅礼书院", 609, 17323, 27106),
    ("二十一中", 609, 17324, 27107),
    ("科大附中", 607, 17877, 27909),
    ("长郡斑马湖", 606, 18130, 28281),
    ("长郡智谷", 603, 19015, 29519),
    ("一中城南", 601, 19540, 30265),
    ("田家炳实验", 600, 19785, 30618),
    ("市十一中融城", 598, 20331, 31350),
    ("明德雨花", 597, 20600, 31686),
    ("稻田", 597, 20600, 31686),
    ("雷锋", 596, 20869, 32023),
    ("附中雨花", 595, 21159, 32379),
    ("麓山外国语", 594, 21450, 32736),
    ("一中广雅", 590, 22594, 34043),
    ("湖大附中", 598, 22877, 34363),
    ("长大附中", 586, 23701, 35272),
    ("雅礼中南附属", 582, 24479, 36377),
    ("岳麓实验", 579, 25619, 37247),
]


SCORE_RANKINGS_2026_NO_QUOTA = [
    (593, 247, 1503),
    (592, 297, 1800),
    (591, 321, 2121),
    (590, 332, 2453),
    (589, 333, 2786),
    (588, 351, 3137),
    (587, 325, 3462),
    (586, 392, 3854),
    (585, 392, 4246),
    (584, 351, 4597),
    (583, 372, 4969),
    (582, 323, 5292),
    (581, 400, 5692),
    (580, 382, 6074),
    (579, 434, 6508),
    (578, 420, 6928),
    (577, 387, 7315),
    (576, 393, 7708),
    (575, 438, 8146),
    (574, 457, 8603),
    (573, 437, 9040),
    (572, 489, 9529),
    (571, 476, 10005),
    (570, 451, 10456),
    (569, 528, 10984),
    (568, 547, 11531),
    (567, 492, 12023),
    (566, 527, 12550),
    (565, 494, 13044),
    (564, 476, 13520),
    (563, 498, 14018),
    (562, 497, 14515),
    (561, 474, 14989),
    (560, 420, 15409),
    (559, 403, 15812),
    (558, 467, 16279),
    (557, 372, 16651),
    (556, 436, 17087),
    (555, 388, 17475),
    (554, 386, 17861),
    (553, 393, 18254),
    (552, 364, 18618),
    (551, 328, 18946),
    (550, 341, 19287),
    (549, 315, 19602),
    (548, 318, 19920),
    (547, 332, 20252),
    (546, 312, 20564),
    (545, 329, 20893),
    (544, 325, 21218),
    (543, 294, 21512),
    (542, 327, 21839),
    (541, 297, 22136),
    (540, 304, 22440),
    (539, 306, 22746),
    (538, 292, 23038),
    (537, 313, 23351),
    (536, 293, 23644),
    (535, 300, 23944),
    (534, 342, 24286),
    (533, 322, 24608),
    (532, 315, 24923),
    (531, 336, 25259),
    (530, 300, 25559),
    (529, 294, 25853),
    (528, 281, 26134),
    (527, 316, 26450),
    (526, 283, 26733),
    (525, 294, 27027),
    (524, 282, 27309),
    (523, 265, 27574),
    (522, 266, 27840),
    (521, 283, 28123),
    (520, 274, 28397),
    (519, 285, 28682),
    (518, 304, 28986),
    (517, 291, 29277),
    (516, 278, 29555),
    (515, 311, 29866),
    (514, 302, 30168),
    (513, 302, 30470),
    (512, 321, 30791),
]


STRUCTURE_CHANGES_2026 = [
    {
        "school_name": "长郡中学新校区",
        "change_type": "new_school",
        "admission_batch": "first",
        "planned_seats": 1000,
        "effective_seats": 500,
        "benchmark": "雅礼新校区",
        "impact_start_rank": 1500,
        "impact_full_rank": 2600,
        "impact_end_rank": 9000,
        "heat_factor": 0.95,
        "note": "第一批次招生，对标雅礼新校区；规划约1000个年级学位，首年暂按50%即500个有效学位估算。",
    },
    {
        "school_name": "南雅中学东校区",
        "change_type": "new_school",
        "admission_batch": "first",
        "planned_seats": 700,
        "effective_seats": 350,
        "benchmark": "低于南雅，接近第一批次腰部学校",
        "impact_start_rank": 3600,
        "impact_full_rank": 6500,
        "impact_end_rank": 13000,
        "heat_factor": 0.85,
        "note": "第一批次招生，预计低于南雅一段但仍处于优质第一批次区间；规划约700个年级学位，首年暂按50%即350个有效学位估算。",
    },
    {
        "school_name": "长郡会展中学",
        "change_type": "new_school",
        "admission_batch": "second",
        "planned_seats": 1000,
        "effective_seats": 500,
        "benchmark": "约10000名附近的第二批次强势公办高中",
        "impact_start_rank": 6500,
        "impact_full_rank": 10000,
        "impact_end_rank": 22000,
        "heat_factor": 0.85,
        "note": "第二批次招生，位置与批次属性更接近强势第二批学校，暂按约10000名附近落位；规划约1000个年级学位，首年暂按50%即500个有效学位估算。",
    },
    {
        "school_name": "雅礼实验中学",
        "change_type": "expansion",
        "admission_batch": "second",
        "planned_seats": 175,
        "effective_seats": 175,
        "benchmark": "本校扩建",
        "impact_start_rank": 6500,
        "impact_full_rank": 8500,
        "impact_end_rank": 16000,
        "heat_factor": 1.0,
        "note": "2026预计新增150-200个高中学位，先取中值175。",
    },
    {
        "school_name": "长郡湘府",
        "change_type": "expansion",
        "admission_batch": "second",
        "planned_seats": 175,
        "effective_seats": 175,
        "benchmark": "本校扩建",
        "impact_start_rank": 13000,
        "impact_full_rank": 16000,
        "impact_end_rank": 23000,
        "heat_factor": 1.0,
        "note": "2026预计新增150-200个高中学位，先取中值175。",
    },
    {
        "school_name": "长铁一中",
        "change_type": "expansion",
        "admission_batch": "second",
        "planned_seats": 175,
        "effective_seats": 175,
        "benchmark": "本校扩建",
        "impact_start_rank": 13000,
        "impact_full_rank": 16500,
        "impact_end_rank": 23000,
        "heat_factor": 1.0,
        "note": "2026预计新增150-200个高中学位，先取中值175。",
    },
    {
        "school_name": "市十五中",
        "change_type": "expansion",
        "admission_batch": "second",
        "planned_seats": 175,
        "effective_seats": 175,
        "benchmark": "本校扩建",
        "impact_start_rank": 14000,
        "impact_full_rank": 17000,
        "impact_end_rank": 23000,
        "heat_factor": 1.0,
        "note": "2026预计新增150-200个高中学位，先取中值175。",
    },
]


FIRST_BATCH_SCHOOLS = {
    "长郡",
    "长郡中学",
    "长郡中学新校区",
    "雅礼",
    "雅礼新",
    "师大附中",
    "师大附中新",
    "市一中",
    "市一中新",
    "明德",
    "周南",
    "市实验",
    "南雅",
    "南雅中学东校区",
    "麓山国际",
}


def initialize_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        create_schema(conn)
        seed_defaults(conn)


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            tier TEXT,
            admission_batch TEXT NOT NULL DEFAULT 'second',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admission_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL REFERENCES schools(id),
            year INTEGER NOT NULL,
            admission_score REAL NOT NULL,
            rank_without_quota INTEGER NOT NULL,
            rank_with_quota INTEGER,
            enrollment_plan INTEGER,
            source_type TEXT NOT NULL DEFAULT 'seed',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(school_id, year)
        );

        CREATE TABLE IF NOT EXISTS score_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            score REAL NOT NULL,
            cumulative_count INTEGER NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'manual',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, score)
        );

        CREATE TABLE IF NOT EXISTS prediction_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            name TEXT NOT NULL,
            reach_min_gap INTEGER NOT NULL,
            reach_max_gap INTEGER NOT NULL,
            target_min_gap INTEGER NOT NULL,
            target_max_gap INTEGER NOT NULL,
            safety_max_gap INTEGER NOT NULL,
            max_items_per_group INTEGER NOT NULL DEFAULT 5,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS year_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL UNIQUE,
            is_current INTEGER NOT NULL DEFAULT 0,
            total_score INTEGER NOT NULL DEFAULT 700,
            admission_data_year INTEGER NOT NULL,
            ranking_table_ready INTEGER NOT NULL DEFAULT 0,
            admission_data_ready INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS structure_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            school_name TEXT NOT NULL,
            change_type TEXT NOT NULL,
            admission_batch TEXT NOT NULL DEFAULT 'second',
            planned_seats INTEGER NOT NULL,
            effective_seats INTEGER NOT NULL,
            benchmark TEXT,
            impact_start_rank INTEGER NOT NULL,
            impact_full_rank INTEGER NOT NULL,
            impact_end_rank INTEGER NOT NULL,
            heat_factor REAL NOT NULL DEFAULT 1.0,
            note TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, school_name, change_type)
        );
        """
    )


def seed_defaults(conn: sqlite3.Connection) -> None:
    ensure_schema(conn)
    conn.execute(
        """
        UPDATE structure_changes
        SET is_active = 0, updated_at = CURRENT_TIMESTAMP
        WHERE year = 2026
          AND school_name = '长郡奥体城校区'
          AND change_type = 'new_school'
        """
    )
    for name, score, rank_without_quota, rank_with_quota in ADMISSIONS_2025:
        tier = estimate_tier(rank_without_quota)
        admission_batch = estimate_batch(name)
        conn.execute(
            "INSERT OR IGNORE INTO schools (name, tier, admission_batch) VALUES (?, ?, ?)",
            (name, tier, admission_batch),
        )
        conn.execute(
            "UPDATE schools SET tier = ?, admission_batch = ? WHERE name = ?",
            (tier, admission_batch, name),
        )
        school_id = conn.execute("SELECT id FROM schools WHERE name = ?", (name,)).fetchone()[0]
        conn.execute(
            """
            INSERT OR IGNORE INTO admission_history
            (school_id, year, admission_score, rank_without_quota, rank_with_quota, source_type)
            VALUES (?, 2025, ?, ?, ?, 'seed')
            """,
            (school_id, score, rank_without_quota, rank_with_quota),
        )

    conn.execute(
        """
        INSERT OR IGNORE INTO prediction_rules
        (year, name, reach_min_gap, reach_max_gap, target_min_gap, target_max_gap, safety_max_gap)
        VALUES (2026, '2026 MVP 默认规则', 1, 300, -500, 0, -501)
        """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO year_configs
        (year, is_current, total_score, admission_data_year, ranking_table_ready, admission_data_ready)
        VALUES (2026, 1, 630, 2025, 0, 1)
        """
    )
    conn.execute(
        """
        UPDATE year_configs
        SET total_score = 630,
            admission_data_year = 2025,
            ranking_table_ready = 1,
            admission_data_ready = 1
        WHERE year = 2026
        """
    )

    for score, segment_count, cumulative_count in SCORE_RANKINGS_2026_NO_QUOTA:
        conn.execute(
            """
            INSERT INTO score_rankings (year, score, cumulative_count, source_type)
            VALUES (2026, ?, ?, 'no_quota_seed')
            ON CONFLICT(year, score) DO UPDATE SET
                cumulative_count = excluded.cumulative_count,
                source_type = excluded.source_type
            """,
            (score, cumulative_count),
        )

    conn.execute("UPDATE structure_changes SET is_active = 0 WHERE year = 2026")
    for change in STRUCTURE_CHANGES_2026:
        conn.execute(
            """
            INSERT INTO structure_changes
            (
                year, school_name, change_type, admission_batch, planned_seats, effective_seats,
                benchmark, impact_start_rank, impact_full_rank, impact_end_rank,
                heat_factor, note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(year, school_name, change_type) DO UPDATE SET
                admission_batch = excluded.admission_batch,
                planned_seats = excluded.planned_seats,
                effective_seats = excluded.effective_seats,
                benchmark = excluded.benchmark,
                impact_start_rank = excluded.impact_start_rank,
                impact_full_rank = excluded.impact_full_rank,
                impact_end_rank = excluded.impact_end_rank,
                heat_factor = excluded.heat_factor,
                note = excluded.note,
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                2026,
                change["school_name"],
                change["change_type"],
                change["admission_batch"],
                change["planned_seats"],
                change["effective_seats"],
                change["benchmark"],
                change["impact_start_rank"],
                change["impact_full_rank"],
                change["impact_end_rank"],
                change["heat_factor"],
                change["note"],
            ),
        )


def ensure_schema(conn: sqlite3.Connection) -> None:
    ensure_column(conn, "schools", "admission_batch", "TEXT NOT NULL DEFAULT 'second'")
    ensure_column(conn, "structure_changes", "admission_batch", "TEXT NOT NULL DEFAULT 'second'")


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def estimate_tier(rank: int) -> str:
    if rank <= 5000:
        return "第一梯队"
    if rank <= 13000:
        return "第二梯队"
    if rank <= 22000:
        return "第三梯队"
    return "第四梯队"


def estimate_batch(name: str) -> str:
    return "first" if name in FIRST_BATCH_SCHOOLS else "second"
