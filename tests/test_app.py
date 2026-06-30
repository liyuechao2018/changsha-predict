from __future__ import annotations

import unittest

import app


class AppRoutingTests(unittest.TestCase):
    def test_normalize_predict_root(self) -> None:
        self.assertEqual(app.normalize_path("/predict"), "/")

    def test_normalize_predict_static(self) -> None:
        self.assertEqual(app.normalize_path("/predict/static/app.js"), "/static/app.js")

    def test_normalize_unprefixed_path(self) -> None:
        self.assertEqual(app.normalize_path("/api/health"), "/api/health")


if __name__ == "__main__":
    unittest.main()
