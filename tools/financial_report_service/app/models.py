from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    partial = "partial"


class FetchStatus(str, Enum):
    downloaded = "downloaded"
    skipped_exists = "skipped_exists"
    failed = "failed"


class ParseStatus(str, Enum):
    parsed = "parsed"
    parsed_no_metric = "parsed_no_metric"
    scanned_skipped = "scanned_skipped"
    skipped_existing = "skipped_existing"
    failed = "failed"


class MetricSource(str, Enum):
    pdf = "pdf"
    akshare = "akshare"
    missing = "missing"


class JobCreateOptions(BaseModel):
    years: int = Field(default=3, ge=1, le=20)
    full_refresh: bool = False
    report_types: List[str] = Field(default_factory=lambda: ["annual", "semi", "q1", "q3"])


class ReportRecord(BaseModel):
    code: str
    name: str = ""
    exchange: str
    announcement_id: str
    title: str
    report_type: str
    report_date: str
    report_period: str
    pdf_url: str
    pdf_path: str
    fetch_status: FetchStatus
    parse_status: ParseStatus


class MetricRecord(BaseModel):
    job_id: str
    code: str
    report_period: str
    metric_name: str
    metric_value: Optional[float]
    unit: str
    source: MetricSource
    confidence: float


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float
    total_codes: int
    done_codes: int
    success_reports: int
    failed_reports: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime
    artifacts: Dict[str, str] = Field(default_factory=dict)


class JobResultsResponse(BaseModel):
    summary: Dict[str, object]
    reports_manifest_path: str
    financial_csv_path: str
    errors_path: str


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: int
