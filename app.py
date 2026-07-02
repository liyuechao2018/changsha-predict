from __future__ import annotations

import json
import logging
import mimetypes
from logging.handlers import RotatingFileHandler
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from config import AppConfig
from database import initialize_database
from prediction_engine import PredictionRequest, PredictionService


CONFIG = AppConfig.from_env()
LOGGER = logging.getLogger("changsha_predict")


class AppHandler(BaseHTTPRequestHandler):
    config = CONFIG
    service = PredictionService(CONFIG.db_path)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = normalize_path(parsed.path, self.config.base_path)
        if path == "/":
            self._serve_file(self.config.static_dir / "index.html")
            return
        if path.startswith("/static/"):
            relative = path.removeprefix("/static/")
            self._serve_file(self.config.static_dir / relative)
            return
        if path == "/api/health":
            self._json({"ok": True})
            return
        self._not_found()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = normalize_path(parsed.path, self.config.base_path)
        if path != "/api/predictions":
            self._not_found()
            return

        try:
            payload = self._read_json()
            request = PredictionRequest(
                year=int(payload.get("year") or 2026),
                score=float(payload.get("score") or 0),
                quality_level=str(payload.get("qualityLevel") or "未填写"),
                rank=int(payload["rank"]) if payload.get("rank") not in (None, "") else None,
            )
            result = self.service.predict(request)
        except ValueError as exc:
            self._json({"error": str(exc)}, status=400)
            return
        except Exception as exc:
            LOGGER.exception("Prediction failed")
            self._json({"error": f"预测失败：{exc}"}, status=500)
            return

        self._json(result)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def _serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._not_found()
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _not_found(self) -> None:
        self._json({"error": "Not found"}, status=404)

    def log_message(self, format: str, *args) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)


def main() -> None:
    configure_logging(CONFIG)
    initialize_database(CONFIG.db_path)
    server = ThreadingHTTPServer((CONFIG.host, CONFIG.port), AppHandler)
    LOGGER.info("Server started at http://%s:%s%s", CONFIG.host, CONFIG.port, CONFIG.base_path or "/")
    print(f"长沙中考录取预测系统已启动：http://{CONFIG.host}:{CONFIG.port}{CONFIG.base_path or ''}")
    server.serve_forever()


def normalize_path(path: str, base_path: str = CONFIG.base_path) -> str:
    if not base_path:
        return path
    if path == base_path:
        return "/"
    if path.startswith(base_path + "/"):
        return path.removeprefix(base_path)
    return path


def configure_logging(config: AppConfig) -> None:
    config.log_dir.mkdir(parents=True, exist_ok=True)
    log_file = config.log_dir / "app.log"
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        handlers=[handler, logging.StreamHandler()],
    )


if __name__ == "__main__":
    main()
