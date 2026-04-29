from __future__ import annotations

import csv
import io
import re
from typing import Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.config import settings
from app.job_manager import JobManager
from app.models import (
    HealthResponse,
    JobCreateOptions,
    JobCreateResponse,
    JobResultsResponse,
    JobStatusResponse,
)


CODE_RE = re.compile(r"^\d{6}$")
ALLOWED_REPORT_TYPES = {"annual", "semi", "q1", "q3"}

router = APIRouter(prefix="/api/v1", tags=["financial-report-jobs"])


def get_job_manager(request: Request) -> JobManager:
    return request.app.state.job_manager


def _decode_csv(content: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail="CSV encoding must be UTF-8/UTF-8-BOM/GBK")


def _parse_report_types(raw: str) -> List[str]:
    items = [x.strip() for x in raw.split(",") if x.strip()]
    if not items:
        items = ["annual", "semi", "q1", "q3"]

    unknown = [x for x in items if x not in ALLOWED_REPORT_TYPES]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report_types: {unknown}. allowed={sorted(ALLOWED_REPORT_TYPES)}",
        )
    return items


def _parse_csv_codes(csv_text: str) -> List[Dict[str, str]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV is empty")

    normalized_fields = {name.strip().lower(): name for name in reader.fieldnames}
    if "code" not in normalized_fields:
        raise HTTPException(status_code=400, detail="CSV requires `code` column")

    code_col = normalized_fields["code"]
    name_col = normalized_fields.get("name")

    seen = set()
    out = []
    errors = []

    for idx, row in enumerate(reader, start=2):
        code = str(row.get(code_col, "")).strip().zfill(6)
        name = str(row.get(name_col, "")).strip() if name_col else ""

        if not CODE_RE.match(code):
            errors.append(f"line {idx}: invalid code `{row.get(code_col, '')}`")
            continue

        if code in seen:
            continue
        seen.add(code)
        out.append({"code": code, "name": name})

    if errors:
        raise HTTPException(status_code=400, detail={"message": "CSV validation failed", "errors": errors})
    if not out:
        raise HTTPException(status_code=400, detail="no valid stock code rows found")
    return out


@router.post("/jobs", response_model=JobCreateResponse)
async def create_job(
    request: Request,
    file: UploadFile = File(...),
    years: int = Form(default=settings.default_years),
    full_refresh: bool = Form(default=False),
    report_types: str = Form(default="annual,semi,q1,q3"),
    manager: JobManager = Depends(get_job_manager),
) -> JobCreateResponse:
    if years < 1 or years > settings.max_years:
        raise HTTPException(status_code=400, detail=f"years must be in [1, {settings.max_years}]")

    raw = await file.read()
    csv_text = _decode_csv(raw)
    code_rows = _parse_csv_codes(csv_text)
    parsed_report_types = _parse_report_types(report_types)

    options = JobCreateOptions(years=years, full_refresh=full_refresh, report_types=parsed_report_types)
    return manager.submit_job(code_rows, options)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, manager: JobManager = Depends(get_job_manager)) -> JobStatusResponse:
    try:
        return manager.get_job_status(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/jobs/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(job_id: str, manager: JobManager = Depends(get_job_manager)) -> JobResultsResponse:
    try:
        return manager.get_job_results(job_id)
    except KeyError as exc:
        msg = str(exc)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=409, detail=msg) from exc


@router.get("/healthz", response_model=HealthResponse)
def healthz(manager: JobManager = Depends(get_job_manager)) -> HealthResponse:
    return HealthResponse(status="ok", version=settings.app_version, uptime_seconds=manager.uptime_seconds)


@router.get("/dashboard/stats")
def dashboard_stats(manager: JobManager = Depends(get_job_manager)):
    return manager.db.get_dashboard_stats()


@router.get("/companies")
def list_companies(manager: JobManager = Depends(get_job_manager)):
    return manager.db.list_companies()


@router.get("/companies/search")
def search_companies(q: str, manager: JobManager = Depends(get_job_manager)):
    if not q.strip():
        return manager.db.list_companies()
    return manager.db.search_companies(q.strip())


@router.get("/companies/{code}/reports")
def list_reports(code: str, manager: JobManager = Depends(get_job_manager)):
    return manager.db.list_reports_for_code(code)


@router.get("/companies/{code}/metrics")
def list_metrics(code: str, manager: JobManager = Depends(get_job_manager)):
    return manager.db.list_metrics_for_code(code)
