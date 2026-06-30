from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class AppConfig:
    host: str
    port: int
    base_path: str
    static_dir: Path
    db_path: Path
    log_dir: Path
    log_level: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_env_file(ROOT / ".env")

        base_path = os.environ.get("BASE_PATH", "/predict").strip()
        if base_path and not base_path.startswith("/"):
            base_path = "/" + base_path
        base_path = base_path.rstrip("/") or ""

        static_dir = Path(os.environ.get("STATIC_DIR", ROOT / "static"))
        db_path = Path(os.environ.get("DB_PATH", ROOT / "data" / "changsha_prediction.db"))
        log_dir = Path(os.environ.get("LOG_DIR", ROOT / "logs"))

        if not static_dir.is_absolute():
            static_dir = ROOT / static_dir
        if not db_path.is_absolute():
            db_path = ROOT / db_path
        if not log_dir.is_absolute():
            log_dir = ROOT / log_dir

        return cls(
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "8000")),
            base_path=base_path,
            static_dir=static_dir,
            db_path=db_path,
            log_dir=log_dir,
            log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        )
