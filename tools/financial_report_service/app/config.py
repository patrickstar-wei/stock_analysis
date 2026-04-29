from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path = Path(__file__).resolve().parents[1]
    output_dir: Path = project_root / "output"
    state_dir: Path = project_root / "state"
    report_index_path: Path = state_dir / "report_index.json"
    db_path: Path = state_dir / "financial_data.db"

    app_name: str = "AShare Financial Report Service"
    app_version: str = "0.1.0"

    cninfo_query_url: str = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    cninfo_pdf_base_url: str = "http://static.cninfo.com.cn/"

    query_retries: int = 3
    download_retries: int = 3
    query_rate_limit_seconds: float = 1.0

    job_workers: int = 2
    pdf_download_workers: int = 2

    default_years: int = 3
    max_years: int = 20

    scanned_text_threshold: int = 1500


settings = Settings()
