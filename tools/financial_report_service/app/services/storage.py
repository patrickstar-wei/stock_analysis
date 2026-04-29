from __future__ import annotations

import csv
import json
import threading
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from app.config import Settings


def should_skip_report(
    report_index: Dict[str, Dict[str, str]],
    announcement_id: str,
    full_refresh: bool,
) -> bool:
    if full_refresh:
        return False
    record = report_index.get(announcement_id)
    if not record:
        return False
    pdf_path = record.get("pdf_path", "")
    if not pdf_path:
        return False
    return Path(pdf_path).exists()


class StorageService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._index_lock = threading.Lock()

    def ensure_dirs(self) -> None:
        self.settings.output_dir.mkdir(parents=True, exist_ok=True)
        self.settings.state_dir.mkdir(parents=True, exist_ok=True)

    def ensure_job_dirs(self, job_id: str) -> Dict[str, Path]:
        self.ensure_dirs()

        base = self.settings.output_dir / job_id
        pdf_dir = base / "pdf"
        base.mkdir(parents=True, exist_ok=True)
        pdf_dir.mkdir(parents=True, exist_ok=True)

        return {
            "base": base,
            "pdf_dir": pdf_dir,
            "manifest": base / "reports_manifest.json",
            "financial_csv": base / "financial_metrics.csv",
            "summary": base / "job_summary.json",
            "errors": base / "errors.jsonl",
        }

    @staticmethod
    def write_json(path: Path, data: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    @staticmethod
    def read_json(path: Path, default: object) -> object:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def write_csv(path: Path, rows: Iterable[Dict[str, object]]) -> None:
        rows = list(rows)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            with path.open("w", encoding="utf-8", newline="") as fh:
                fh.write("")
            return

        fieldnames = list(rows[0].keys())
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    @staticmethod
    def append_jsonl(path: Path, item: Dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    def load_report_index(self) -> Dict[str, Dict[str, str]]:
        self.ensure_dirs()
        with self._index_lock:
            data = self.read_json(self.settings.report_index_path, default={})
            if isinstance(data, dict):
                return data
            return {}

    def save_report_index(self, report_index: Dict[str, Dict[str, str]]) -> None:
        self.ensure_dirs()
        with self._index_lock:
            self.write_json(self.settings.report_index_path, report_index)
