from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from app.clients.akshare_client import AkshareClient, AkMetric
from app.clients.cninfo_client import CninfoAnnouncement, CninfoClient
from app.clients.efinance_client import EfinanceClient
from app.config import Settings
from app.models import (
    FetchStatus,
    JobCreateOptions,
    JobCreateResponse,
    JobResultsResponse,
    JobStatus,
    JobStatusResponse,
    MetricRecord,
    ParseStatus,
    ReportRecord,
)
from app.services.database import FinancialDatabase
from app.services.extractor import METRIC_NAMES, MetricExtractor
from app.services.pdf_parser import PDFParser
from app.services.storage import StorageService, should_skip_report


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


API_SUFFICIENT_RATIO = 0.6


@dataclass
class JobState:
    job_id: str
    options: JobCreateOptions
    total_codes: int
    created_at: datetime
    status: JobStatus = JobStatus.queued
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    done_codes: int = 0
    success_reports: int = 0
    failed_reports: int = 0
    cached_reports: int = 0
    api_only_reports: int = 0
    artifacts: Dict[str, str] = field(default_factory=dict)
    summary: Dict[str, object] = field(default_factory=dict)

    def to_status_response(self) -> JobStatusResponse:
        progress = 0.0
        if self.total_codes > 0:
            progress = round(self.done_codes / self.total_codes, 4)
        return JobStatusResponse(
            job_id=self.job_id,
            status=self.status,
            progress=progress,
            total_codes=self.total_codes,
            done_codes=self.done_codes,
            success_reports=self.success_reports,
            failed_reports=self.failed_reports,
            started_at=self.started_at,
            finished_at=self.finished_at,
            created_at=self.created_at,
            artifacts=self.artifacts,
        )


class JobManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.storage = StorageService(settings)
        self.cninfo = CninfoClient(settings)
        self.akshare = AkshareClient()
        self.efinance = EfinanceClient()
        self.pdf_parser = PDFParser(settings)
        self.extractor = MetricExtractor()
        self.db = FinancialDatabase(settings)

        self._jobs: Dict[str, JobState] = {}
        self._jobs_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=self.settings.job_workers)
        self._service_started_at = utc_now()

    @property
    def uptime_seconds(self) -> int:
        return int((utc_now() - self._service_started_at).total_seconds())

    def submit_job(self, code_records: List[Dict[str, str]], options: JobCreateOptions) -> JobCreateResponse:
        job_id = uuid.uuid4().hex
        state = JobState(
            job_id=job_id,
            options=options,
            total_codes=len(code_records),
            created_at=utc_now(),
            status=JobStatus.queued,
        )

        with self._jobs_lock:
            self._jobs[job_id] = state

        self._executor.submit(self._run_job, state, code_records)
        return JobCreateResponse(job_id=job_id, status=state.status, created_at=state.created_at)

    def get_job_status(self, job_id: str) -> JobStatusResponse:
        state = self._get_state(job_id)
        return state.to_status_response()

    def get_job_results(self, job_id: str) -> JobResultsResponse:
        state = self._get_state(job_id)
        if not state.artifacts:
            raise KeyError("artifacts are not available yet")

        return JobResultsResponse(
            summary=state.summary,
            reports_manifest_path=state.artifacts.get("reports_manifest_path", ""),
            financial_csv_path=state.artifacts.get("financial_csv_path", ""),
            errors_path=state.artifacts.get("errors_path", ""),
        )

    def _get_state(self, job_id: str) -> JobState:
        with self._jobs_lock:
            state = self._jobs.get(job_id)
        if state is None:
            raise KeyError(f"job not found: {job_id}")
        return state

    def _append_error(self, errors_path: Path, code: str, stage: str, message: str) -> None:
        self.storage.append_jsonl(
            errors_path,
            {
                "ts": utc_now().isoformat(),
                "code": code,
                "stage": stage,
                "message": message,
            },
        )

    @staticmethod
    def _select_ak_metrics(ak_metrics_by_period: Dict[str, Dict[str, AkMetric]], report_period: str) -> Dict[str, AkMetric]:
        if not ak_metrics_by_period:
            return {}
        if report_period in ak_metrics_by_period:
            return ak_metrics_by_period[report_period]

        if "" in ak_metrics_by_period:
            return ak_metrics_by_period[""]

        keys = sorted([k for k in ak_metrics_by_period.keys() if k])
        if not keys:
            return {}

        candidates = [k for k in keys if k <= report_period]
        if candidates:
            return ak_metrics_by_period[candidates[-1]]
        return ak_metrics_by_period[keys[-1]]

    @staticmethod
    def _count_non_missing(metrics: Dict[str, Dict[str, object]]) -> int:
        return sum(1 for m in metrics.values() if m.get("value") is not None)

    def _build_metric_records_from_db(
        self,
        job_id: str,
        code: str,
        report_period: str,
        db_metrics: Dict[str, Dict[str, object]],
    ) -> List[MetricRecord]:
        records = []
        for metric_name in METRIC_NAMES:
            item = db_metrics.get(metric_name, {
                "value": None,
                "unit": "%" if metric_name in {"ROE", "资产负债率", "毛利率", "研发占比"} else "元",
                "source": "missing",
                "confidence": 0.0,
            })
            records.append(
                MetricRecord(
                    job_id=job_id,
                    code=code,
                    report_period=report_period,
                    metric_name=metric_name,
                    metric_value=item.get("value"),
                    unit=item.get("unit", "元"),
                    source=item.get("source", "missing"),
                    confidence=item.get("confidence", 0.0),
                )
            )
        return records

    def _download_reports_concurrently(
        self,
        announcements: Sequence[CninfoAnnouncement],
        pdf_dir: Path,
        report_index: Dict[str, Dict[str, str]],
        full_refresh: bool,
        errors_path: Path,
    ) -> Dict[str, Dict[str, object]]:
        output: Dict[str, Dict[str, object]] = {}
        futures = {}

        with ThreadPoolExecutor(max_workers=self.settings.pdf_download_workers) as dl_executor:
            for ann in announcements:
                pdf_path = pdf_dir / ann.code / f"{ann.announcement_id}.pdf"
                if should_skip_report(report_index, ann.announcement_id, full_refresh):
                    output[ann.announcement_id] = {
                        "fetch_status": FetchStatus.skipped_exists,
                        "pdf_path": Path(report_index[ann.announcement_id]["pdf_path"]),
                    }
                    continue

                future = dl_executor.submit(self.cninfo.download_pdf, ann.adjunct_url, pdf_path)
                futures[future] = (ann, pdf_path)

            for future in as_completed(futures):
                ann, pdf_path = futures[future]
                try:
                    future.result()
                    output[ann.announcement_id] = {
                        "fetch_status": FetchStatus.downloaded,
                        "pdf_path": pdf_path,
                    }
                except Exception as exc:
                    self._append_error(errors_path, ann.code, "download_pdf", str(exc))
                    output[ann.announcement_id] = {
                        "fetch_status": FetchStatus.failed,
                        "pdf_path": pdf_path,
                        "error_message": str(exc),
                    }

        return output

    def _save_to_database(
        self,
        code: str,
        name: str,
        exchange: str,
        ann: CninfoAnnouncement,
        pdf_path: str,
        fetch_status: str,
        parse_status: str,
        merged: Dict[str, Dict[str, object]],
        now_iso: str,
    ) -> None:
        self.db.upsert_company(code, name, exchange, now_iso)
        self.db.upsert_report(
            announcement_id=ann.announcement_id,
            code=code,
            name=name,
            exchange=exchange,
            title=ann.title,
            report_type=ann.report_type,
            report_date=ann.report_date,
            report_period=ann.report_period,
            pdf_url=ann.pdf_url,
            pdf_path=pdf_path,
            fetch_status=fetch_status,
            parse_status=parse_status,
            now=now_iso,
        )
        metrics_rows = []
        for metric_name, item in merged.items():
            metrics_rows.append({
                "metric_name": metric_name,
                "metric_value": item.get("value"),
                "unit": item.get("unit", "元"),
                "source": item.get("source", "missing"),
                "confidence": item.get("confidence", 0.0),
            })
        self.db.upsert_metrics_batch(code, ann.report_period, metrics_rows, now_iso)

    def _save_api_only_periods(
        self,
        code: str,
        name: str,
        exchange: str,
        ak_metrics_by_period: Dict[str, Dict[str, AkMetric]],
        ef_metrics: Dict[str, AkMetric],
        state: JobState,
        dirs: Dict[str, Path],
        manifest_records: List[ReportRecord],
        metric_records: List[MetricRecord],
        now_iso: str,
    ) -> None:
        from app.models import MetricSource

        self.db.upsert_company(code, name, exchange, now_iso)

        for period, ak_metrics in sorted(ak_metrics_by_period.items()):
            api_merged = self._merge_api_metrics({}, ak_metrics, ef_metrics)
            api_non_missing = self._count_non_missing(api_merged)
            if api_non_missing < len(METRIC_NAMES) * API_SUFFICIENT_RATIO:
                continue

            ann_id = f"api_{code}_{period.replace('-', '')}"
            self.db.upsert_report(
                announcement_id=ann_id,
                code=code,
                name=name,
                exchange=exchange,
                title=f"API数据-{period}",
                report_type="api",
                report_date=period,
                report_period=period,
                pdf_url="",
                pdf_path="",
                fetch_status="api_only",
                parse_status="api_only",
                now=now_iso,
            )
            metrics_rows = []
            for metric_name, item in api_merged.items():
                metrics_rows.append({
                    "metric_name": metric_name,
                    "metric_value": item.get("value"),
                    "unit": item.get("unit", "元"),
                    "source": item.get("source", "missing"),
                    "confidence": item.get("confidence", 0.0),
                })
            self.db.upsert_metrics_batch(code, period, metrics_rows, now_iso)

            for metric_name in METRIC_NAMES:
                item = api_merged[metric_name]
                metric_records.append(
                    MetricRecord(
                        job_id=state.job_id,
                        code=code,
                        report_period=period,
                        metric_name=metric_name,
                        metric_value=item["value"],
                        unit=item["unit"],
                        source=item["source"],
                        confidence=item["confidence"],
                    )
                )

            manifest_records.append(
                ReportRecord(
                    code=code,
                    name=name,
                    exchange=exchange,
                    announcement_id=ann_id,
                    title=f"API数据-{period}",
                    report_type="api",
                    report_date=period,
                    report_period=period,
                    pdf_url="",
                    pdf_path="",
                    fetch_status=FetchStatus.skipped_exists,
                    parse_status=ParseStatus.skipped_existing,
                )
            )
            state.api_only_reports += 1
            state.success_reports += 1

    def _merge_api_metrics(
        self,
        base: Dict[str, Dict[str, object]],
        ak_metrics: Dict[str, AkMetric],
        ef_metrics: Dict[str, AkMetric],
    ) -> Dict[str, Dict[str, object]]:
        """Merge metrics: existing data > akshare > efinance > missing."""
        from app.models import MetricSource

        merged: Dict[str, Dict[str, object]] = {}
        for metric_name in METRIC_NAMES:
            if metric_name in base and base[metric_name].get("value") is not None:
                merged[metric_name] = base[metric_name]
                continue

            ak = ak_metrics.get(metric_name)
            if ak is not None:
                merged[metric_name] = {
                    "value": float(ak.value),
                    "unit": ak.unit,
                    "source": MetricSource.akshare.value,
                    "confidence": 0.7,
                }
                continue

            ef = ef_metrics.get(metric_name)
            if ef is not None:
                merged[metric_name] = {
                    "value": float(ef.value),
                    "unit": ef.unit,
                    "source": MetricSource.efinance.value,
                    "confidence": 0.6,
                }
                continue

            merged[metric_name] = {
                "value": None,
                "unit": "%" if metric_name in {"ROE", "资产负债率", "毛利率", "研发占比"} else "元",
                "source": MetricSource.missing.value,
                "confidence": 0.0,
            }
        return merged

    def _run_job(self, state: JobState, code_records: List[Dict[str, str]]) -> None:
        dirs = self.storage.ensure_job_dirs(state.job_id)
        report_index = self.storage.load_report_index()

        manifest_records: List[ReportRecord] = []
        metric_records: List[MetricRecord] = []

        state.status = JobStatus.running
        state.started_at = utc_now()

        try:
            for row in code_records:
                code = row["code"]
                requested_name = row.get("name", "")
                now_iso = utc_now().isoformat()

                cached_name = self.db.get_company_name(code)
                name = requested_name or cached_name or self.akshare.lookup_stock_name(code)

                if state.options.full_refresh:
                    self.db.delete_metrics_for_code(code)
                    self.db.delete_reports_for_code(code)

                try:
                    announcements = self.cninfo.query_announcements(
                        code=code,
                        name=name,
                        years=state.options.years,
                        report_types=state.options.report_types,
                    )
                except Exception as exc:
                    self._append_error(dirs["errors"], code, "query_announcements", str(exc))
                    state.failed_reports += 1
                    state.done_codes += 1
                    continue

                if not announcements:
                    if not state.options.full_refresh:
                        db_all = self.db.get_all_metrics_for_code(code)
                        if db_all:
                            for period, db_metrics in db_all.items():
                                if self._count_non_missing(db_metrics) >= len(METRIC_NAMES) * 0.5:
                                    metric_records.extend(
                                        self._build_metric_records_from_db(
                                            state.job_id, code, period, db_metrics
                                        )
                                    )
                                    state.cached_reports += 1
                                    state.success_reports += 1
                            if state.cached_reports > 0:
                                state.done_codes += 1
                                continue

                    ak_metrics_by_period, ak_status = self.akshare.get_financial_metrics_by_period(code)
                    ef_metrics, ef_status = self.efinance.get_latest_metrics(code)

                    if ak_status == "akshare_ok" and ak_metrics_by_period:
                        self._save_api_only_periods(
                            code, name, "", ak_metrics_by_period, ef_metrics,
                            state, dirs, manifest_records, metric_records, now_iso,
                        )
                        state.done_codes += 1
                        continue

                    self._append_error(dirs["errors"], code, "query_announcements", "no announcements and no API data")
                    state.failed_reports += 1
                    state.done_codes += 1
                    continue

                ak_metrics_by_period: Dict[str, Dict[str, AkMetric]] = {}
                ef_metrics: Dict[str, AkMetric] = {}

                need_api = False
                for ann in announcements:
                    if not state.options.full_refresh:
                        db_metrics = self.db.get_metrics_for_period(code, ann.report_period)
                        if db_metrics and self._count_non_missing(db_metrics) >= len(METRIC_NAMES) * 0.5:
                            metric_records.extend(
                                self._build_metric_records_from_db(
                                    state.job_id, code, ann.report_period, db_metrics
                                )
                            )
                            db_report = self.db.get_report_by_announcement_id(ann.announcement_id)
                            manifest_records.append(
                                ReportRecord(
                                    code=code,
                                    name=name,
                                    exchange=ann.exchange,
                                    announcement_id=ann.announcement_id,
                                    title=ann.title,
                                    report_type=ann.report_type,
                                    report_date=ann.report_date,
                                    report_period=ann.report_period,
                                    pdf_url=ann.pdf_url,
                                    pdf_path=db_report.get("pdf_path", "") if db_report else "",
                                    fetch_status=FetchStatus.skipped_exists,
                                    parse_status=ParseStatus.skipped_existing,
                                )
                            )
                            state.cached_reports += 1
                            state.success_reports += 1
                            continue
                    need_api = True

                if need_api:
                    ak_metrics_by_period, ak_status = self.akshare.get_financial_metrics_by_period(code)
                    if ak_status != "akshare_ok":
                        self._append_error(dirs["errors"], code, "akshare", ak_status)

                    ef_metrics, ef_status = self.efinance.get_latest_metrics(code)
                    if ef_status != "efinance_ok":
                        self._append_error(dirs["errors"], code, "efinance", ef_status)

                announcements_needing_data = []
                for ann in announcements:
                    if not state.options.full_refresh:
                        db_metrics = self.db.get_metrics_for_period(code, ann.report_period)
                        if db_metrics and self._count_non_missing(db_metrics) >= len(METRIC_NAMES) * 0.5:
                            continue
                    announcements_needing_data.append(ann)

                announcements_to_download = []
                for ann in announcements_needing_data:
                    ak_metrics = self._select_ak_metrics(ak_metrics_by_period, ann.report_period)
                    api_merged = self._merge_api_metrics({}, ak_metrics, ef_metrics)
                    api_non_missing = self._count_non_missing(api_merged)

                    if api_non_missing >= len(METRIC_NAMES) * API_SUFFICIENT_RATIO:
                        self.db.upsert_company(code, name, ann.exchange, now_iso)
                        self.db.upsert_report(
                            announcement_id=ann.announcement_id,
                            code=code,
                            name=name,
                            exchange=ann.exchange,
                            title=ann.title,
                            report_type=ann.report_type,
                            report_date=ann.report_date,
                            report_period=ann.report_period,
                            pdf_url=ann.pdf_url,
                            pdf_path="",
                            fetch_status="api_only",
                            parse_status="api_only",
                            now=now_iso,
                        )
                        metrics_rows = []
                        for metric_name, item in api_merged.items():
                            metrics_rows.append({
                                "metric_name": metric_name,
                                "metric_value": item.get("value"),
                                "unit": item.get("unit", "元"),
                                "source": item.get("source", "missing"),
                                "confidence": item.get("confidence", 0.0),
                            })
                        self.db.upsert_metrics_batch(code, ann.report_period, metrics_rows, now_iso)

                        for metric_name in METRIC_NAMES:
                            item = api_merged[metric_name]
                            metric_records.append(
                                MetricRecord(
                                    job_id=state.job_id,
                                    code=code,
                                    report_period=ann.report_period,
                                    metric_name=metric_name,
                                    metric_value=item["value"],
                                    unit=item["unit"],
                                    source=item["source"],
                                    confidence=item["confidence"],
                                )
                            )

                        manifest_records.append(
                            ReportRecord(
                                code=ann.code,
                                name=ann.name or name,
                                exchange=ann.exchange,
                                announcement_id=ann.announcement_id,
                                title=ann.title,
                                report_type=ann.report_type,
                                report_date=ann.report_date,
                                report_period=ann.report_period,
                                pdf_url=ann.pdf_url,
                                pdf_path="",
                                fetch_status=FetchStatus.skipped_exists,
                                parse_status=ParseStatus.skipped_existing,
                            )
                        )
                        state.api_only_reports += 1
                        state.success_reports += 1
                    else:
                        announcements_to_download.append(ann)

                if announcements_to_download:
                    dl_map = self._download_reports_concurrently(
                        announcements=announcements_to_download,
                        pdf_dir=dirs["pdf_dir"],
                        report_index=report_index,
                        full_refresh=state.options.full_refresh,
                        errors_path=dirs["errors"],
                    )

                    for ann in announcements_to_download:
                        dl_result = dl_map.get(ann.announcement_id)
                        if dl_result is None:
                            state.failed_reports += 1
                            self._append_error(
                                dirs["errors"],
                                code,
                                "download_pdf",
                                f"missing download result for {ann.announcement_id}",
                            )
                            continue

                        fetch_status = dl_result["fetch_status"]
                        pdf_path = Path(dl_result["pdf_path"])

                        if fetch_status == FetchStatus.failed:
                            state.failed_reports += 1
                            manifest_records.append(
                                ReportRecord(
                                    code=ann.code,
                                    name=ann.name or name,
                                    exchange=ann.exchange,
                                    announcement_id=ann.announcement_id,
                                    title=ann.title,
                                    report_type=ann.report_type,
                                    report_date=ann.report_date,
                                    report_period=ann.report_period,
                                    pdf_url=ann.pdf_url,
                                    pdf_path=str(pdf_path),
                                    fetch_status=fetch_status,
                                    parse_status=ParseStatus.failed,
                                )
                            )
                            continue

                        parse_status = ParseStatus.parsed
                        pdf_metrics = {}
                        text_result = None
                        try:
                            text_result = self.pdf_parser.extract_text(pdf_path)
                            pdf_metrics = self.extractor.extract_from_text(text_result.text)

                            if text_result.scanned_suspected and len(pdf_metrics) < 3:
                                parse_status = ParseStatus.scanned_skipped
                                pdf_metrics = {}
                            elif not pdf_metrics:
                                parse_status = ParseStatus.parsed_no_metric
                            elif fetch_status == FetchStatus.skipped_exists:
                                parse_status = ParseStatus.skipped_existing
                        except Exception as exc:
                            parse_status = ParseStatus.failed
                            self._append_error(dirs["errors"], code, "parse_pdf", str(exc))

                        ak_metrics = self._select_ak_metrics(ak_metrics_by_period, ann.report_period)
                        merged = self._merge_api_metrics(
                            self.extractor.merge_metrics(pdf_metrics=pdf_metrics, ak_metrics=ak_metrics),
                            {},
                            ef_metrics,
                        )

                        self._save_to_database(
                            code=code,
                            name=ann.name or name,
                            exchange=ann.exchange,
                            ann=ann,
                            pdf_path=str(pdf_path),
                            fetch_status=fetch_status.value if isinstance(fetch_status, FetchStatus) else fetch_status,
                            parse_status=parse_status.value if isinstance(parse_status, ParseStatus) else parse_status,
                            merged=merged,
                            now_iso=now_iso,
                        )

                        for metric_name in METRIC_NAMES:
                            item = merged[metric_name]
                            metric_records.append(
                                MetricRecord(
                                    job_id=state.job_id,
                                    code=code,
                                    report_period=ann.report_period,
                                    metric_name=metric_name,
                                    metric_value=item["value"],
                                    unit=item["unit"],
                                    source=item["source"],
                                    confidence=item["confidence"],
                                )
                            )

                        manifest_records.append(
                            ReportRecord(
                                code=ann.code,
                                name=ann.name or name,
                                exchange=ann.exchange,
                                announcement_id=ann.announcement_id,
                                title=ann.title,
                                report_type=ann.report_type,
                                report_date=ann.report_date,
                                report_period=ann.report_period,
                                pdf_url=ann.pdf_url,
                                pdf_path=str(pdf_path),
                                fetch_status=fetch_status,
                                parse_status=parse_status,
                            )
                        )

                        report_index[ann.announcement_id] = {
                            "code": ann.code,
                            "name": ann.name or name,
                            "pdf_path": str(pdf_path),
                            "report_period": ann.report_period,
                            "updated_at": utc_now().isoformat(),
                        }

                        if parse_status in {ParseStatus.parsed, ParseStatus.parsed_no_metric, ParseStatus.skipped_existing, ParseStatus.scanned_skipped}:
                            state.success_reports += 1
                        else:
                            state.failed_reports += 1

                state.done_codes += 1

            manifest_payload = [item.model_dump() for item in manifest_records]
            metric_payload = [item.model_dump() for item in metric_records]

            self.storage.write_json(dirs["manifest"], manifest_payload)
            self.storage.write_csv(dirs["financial_csv"], metric_payload)
            self.storage.save_report_index(report_index)

            summary = {
                "job_id": state.job_id,
                "status": state.status.value,
                "created_at": state.created_at.isoformat(),
                "started_at": state.started_at.isoformat() if state.started_at else None,
                "finished_at": utc_now().isoformat(),
                "total_codes": state.total_codes,
                "done_codes": state.done_codes,
                "success_reports": state.success_reports,
                "failed_reports": state.failed_reports,
                "cached_reports": state.cached_reports,
                "api_only_reports": state.api_only_reports,
                "manifest_count": len(manifest_records),
                "metric_count": len(metric_records),
            }
            self.storage.write_json(dirs["summary"], summary)

            state.summary = summary
            state.artifacts = {
                "reports_manifest_path": str(dirs["manifest"]),
                "financial_csv_path": str(dirs["financial_csv"]),
                "errors_path": str(dirs["errors"]),
                "summary_path": str(dirs["summary"]),
            }

            if state.success_reports == 0 and state.failed_reports > 0:
                state.status = JobStatus.failed
            elif state.failed_reports == 0:
                state.status = JobStatus.succeeded
            else:
                state.status = JobStatus.partial

        except Exception as exc:
            self._append_error(dirs["errors"], "", "job", str(exc))
            state.status = JobStatus.failed
        finally:
            state.finished_at = utc_now()
            if state.summary:
                state.summary["status"] = state.status.value
                state.summary["finished_at"] = state.finished_at.isoformat()
                self.storage.write_json(dirs["summary"], state.summary)
