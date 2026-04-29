from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.config import Settings


class FinancialDatabase:
    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS companies (
        code        TEXT PRIMARY KEY,
        name        TEXT NOT NULL DEFAULT '',
        exchange    TEXT NOT NULL DEFAULT '',
        created_at  TEXT NOT NULL DEFAULT '',
        updated_at  TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS reports (
        announcement_id TEXT PRIMARY KEY,
        code            TEXT NOT NULL,
        name            TEXT NOT NULL DEFAULT '',
        exchange        TEXT NOT NULL DEFAULT '',
        title           TEXT NOT NULL DEFAULT '',
        report_type     TEXT NOT NULL,
        report_date     TEXT NOT NULL DEFAULT '',
        report_period   TEXT NOT NULL,
        pdf_url         TEXT NOT NULL DEFAULT '',
        pdf_path        TEXT NOT NULL DEFAULT '',
        fetch_status    TEXT NOT NULL DEFAULT '',
        parse_status    TEXT NOT NULL DEFAULT '',
        created_at      TEXT NOT NULL DEFAULT '',
        updated_at      TEXT NOT NULL DEFAULT '',
        FOREIGN KEY (code) REFERENCES companies(code)
    );

    CREATE INDEX IF NOT EXISTS idx_reports_code ON reports(code);
    CREATE INDEX IF NOT EXISTS idx_reports_code_period ON reports(code, report_period);

    CREATE TABLE IF NOT EXISTS metrics (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        code            TEXT NOT NULL,
        report_period   TEXT NOT NULL,
        metric_name     TEXT NOT NULL,
        metric_value    REAL,
        unit            TEXT NOT NULL DEFAULT '',
        source          TEXT NOT NULL DEFAULT '',
        confidence      REAL NOT NULL DEFAULT 0.0,
        created_at      TEXT NOT NULL DEFAULT '',
        updated_at      TEXT NOT NULL DEFAULT '',
        FOREIGN KEY (code) REFERENCES companies(code),
        UNIQUE(code, report_period, metric_name, source)
    );

    CREATE INDEX IF NOT EXISTS idx_metrics_code_period ON metrics(code, report_period);
    CREATE INDEX IF NOT EXISTS idx_metrics_code_period_source ON metrics(code, report_period, source);
    """

    def __init__(self, settings: Settings):
        self.db_path = settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_lock = threading.Lock()
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30,
            )
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA busy_timeout=5000")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _ensure_schema(self) -> None:
        with self._init_lock:
            conn = self._get_conn()
            conn.executescript(self.SCHEMA_SQL)
            conn.commit()

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    def upsert_company(self, code: str, name: str, exchange: str, now: str) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO companies (code, name, exchange, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(code) DO UPDATE SET
                   name=excluded.name, exchange=excluded.exchange, updated_at=excluded.updated_at""",
            (code, name, exchange, now, now),
        )
        conn.commit()

    def upsert_report(
        self,
        announcement_id: str,
        code: str,
        name: str,
        exchange: str,
        title: str,
        report_type: str,
        report_date: str,
        report_period: str,
        pdf_url: str,
        pdf_path: str,
        fetch_status: str,
        parse_status: str,
        now: str,
    ) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO reports (announcement_id, code, name, exchange, title,
                   report_type, report_date, report_period, pdf_url, pdf_path,
                   fetch_status, parse_status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(announcement_id) DO UPDATE SET
                   name=excluded.name, exchange=excluded.exchange,
                   title=excluded.title, report_type=excluded.report_type,
                   report_date=excluded.report_date, report_period=excluded.report_period,
                   pdf_url=excluded.pdf_url, pdf_path=excluded.pdf_path,
                   fetch_status=excluded.fetch_status, parse_status=excluded.parse_status,
                   updated_at=excluded.updated_at""",
            (announcement_id, code, name, exchange, title, report_type,
             report_date, report_period, pdf_url, pdf_path, fetch_status,
             parse_status, now, now),
        )
        conn.commit()

    def upsert_metrics_batch(
        self,
        code: str,
        report_period: str,
        metrics: List[Dict[str, object]],
        now: str,
    ) -> None:
        conn = self._get_conn()
        rows = []
        for m in metrics:
            rows.append((
                code,
                report_period,
                m["metric_name"],
                m.get("metric_value"),
                m.get("unit", ""),
                m.get("source", ""),
                m.get("confidence", 0.0),
                now,
                now,
            ))
        conn.executemany(
            """INSERT INTO metrics (code, report_period, metric_name, metric_value,
                   unit, source, confidence, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(code, report_period, metric_name, source) DO UPDATE SET
                   metric_value=excluded.metric_value, unit=excluded.unit,
                   confidence=excluded.confidence, updated_at=excluded.updated_at""",
            rows,
        )
        conn.commit()

    def get_report_by_announcement_id(self, announcement_id: str) -> Optional[Dict[str, str]]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM reports WHERE announcement_id = ?",
            (announcement_id,),
        ).fetchone()
        return dict(row) if row else None

    def has_report_for_period(self, code: str, report_period: str) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM reports WHERE code = ? AND report_period = ? LIMIT 1",
            (code, report_period),
        ).fetchone()
        return row is not None

    def get_metrics_for_period(
        self, code: str, report_period: str
    ) -> Dict[str, Dict[str, object]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT metric_name, metric_value, unit, source, confidence "
            "FROM metrics WHERE code = ? AND report_period = ?",
            (code, report_period),
        ).fetchall()
        result: Dict[str, Dict[str, object]] = {}
        for row in rows:
            result[row["metric_name"]] = {
                "value": row["metric_value"],
                "unit": row["unit"],
                "source": row["source"],
                "confidence": row["confidence"],
            }
        return result

    def get_all_metrics_for_code(
        self, code: str
    ) -> Dict[str, Dict[str, Dict[str, object]]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT report_period, metric_name, metric_value, unit, source, confidence "
            "FROM metrics WHERE code = ?",
            (code,),
        ).fetchall()
        result: Dict[str, Dict[str, Dict[str, object]]] = {}
        for row in rows:
            period = row["report_period"]
            if period not in result:
                result[period] = {}
            result[period][row["metric_name"]] = {
                "value": row["metric_value"],
                "unit": row["unit"],
                "source": row["source"],
                "confidence": row["confidence"],
            }
        return result

    def get_cached_periods(self, code: str) -> List[str]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT DISTINCT report_period FROM metrics WHERE code = ? ORDER BY report_period",
            (code,),
        ).fetchall()
        return [row["report_period"] for row in rows]

    def get_company_name(self, code: str) -> Optional[str]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT name FROM companies WHERE code = ?",
            (code,),
        ).fetchone()
        return row["name"] if row else None

    def list_companies(self) -> List[Dict[str, str]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT c.code, c.name, c.exchange, "
            "  (SELECT COUNT(DISTINCT m.report_period) FROM metrics m WHERE m.code = c.code) AS period_count, "
            "  (SELECT COUNT(*) FROM metrics m WHERE m.code = c.code) AS metric_count, "
            "  c.updated_at "
            "FROM companies c ORDER BY c.updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_reports_for_code(self, code: str) -> List[Dict[str, str]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT announcement_id, code, name, title, report_type, report_date, "
            "  report_period, pdf_url, fetch_status, parse_status, updated_at "
            "FROM reports WHERE code = ? ORDER BY report_period DESC",
            (code,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_metrics_for_code(self, code: str) -> List[Dict[str, object]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT report_period, metric_name, metric_value, unit, source, confidence "
            "FROM metrics WHERE code = ? ORDER BY report_period DESC, metric_name",
            (code,),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_companies(self, keyword: str) -> List[Dict[str, str]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT c.code, c.name, c.exchange, "
            "  (SELECT COUNT(DISTINCT m.report_period) FROM metrics m WHERE m.code = c.code) AS period_count, "
            "  (SELECT COUNT(*) FROM metrics m WHERE m.code = c.code) AS metric_count, "
            "  c.updated_at "
            "FROM companies c WHERE c.code LIKE ? OR c.name LIKE ? "
            "ORDER BY c.updated_at DESC",
            (f"%{keyword}%", f"%{keyword}%"),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_dashboard_stats(self) -> Dict[str, int]:
        conn = self._get_conn()
        company_count = conn.execute("SELECT COUNT(*) AS cnt FROM companies").fetchone()["cnt"]
        report_count = conn.execute("SELECT COUNT(*) AS cnt FROM reports").fetchone()["cnt"]
        metric_count = conn.execute("SELECT COUNT(*) AS cnt FROM metrics").fetchone()["cnt"]
        cached_count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reports WHERE fetch_status = 'skipped_exists'"
        ).fetchone()["cnt"]
        return {
            "company_count": company_count,
            "report_count": report_count,
            "metric_count": metric_count,
            "cached_count": cached_count,
        }
