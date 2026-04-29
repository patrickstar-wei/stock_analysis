from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import requests

from app.config import Settings


HTML_TAG_RE = re.compile(r"<[^>]+>")
YEAR_RE = re.compile(r"(20\d{2})年")


@dataclass(frozen=True)
class CninfoAnnouncement:
    code: str
    name: str
    exchange: str
    announcement_id: str
    title: str
    report_type: str
    report_date: str
    report_period: str
    pdf_url: str
    adjunct_url: str


class CninfoClient:
    """Client for cninfo announcement search and PDF download."""

    REPORT_CATEGORY_MAP: Dict[str, str] = {
        "annual": "category_ndbg_szsh",
        "semi": "category_bndbg_szsh",
        "q1": "category_yjdbg_szsh",
        "q3": "category_sjdbg_szsh",
    }

    INCLUDE_KEYWORDS: Tuple[str, ...] = (
        "年度报告",
        "半年度报告",
        "第一季度报告",
        "第三季度报告",
    )

    EXCLUDE_KEYWORDS: Tuple[str, ...] = (
        "摘要",
        "英文",
        "取消",
        "审计报告",
        "意见",
        "补充",
        "修订",
    )

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self._lock = threading.Lock()
        self._last_query_ts = 0.0

    @staticmethod
    def map_exchange(code: str) -> Tuple[str, str, str]:
        """Return (column, plate, exchange_label)."""
        if code.startswith("6"):
            return "sse", "sh", "SSE"
        return "szse", "sz", "SZSE"

    @staticmethod
    def strip_html(text: str) -> str:
        return HTML_TAG_RE.sub("", text or "")

    @classmethod
    def detect_report_type(cls, title: str) -> Optional[str]:
        t = cls.strip_html(title)
        if "第一季度报告" in t:
            return "q1"
        if "第三季度报告" in t:
            return "q3"
        if "半年度报告" in t:
            return "semi"
        if "年度报告" in t:
            return "annual"
        return None

    @classmethod
    def infer_report_period(cls, title: str, report_type: str, fallback_report_date: str) -> str:
        t = cls.strip_html(title)
        m = YEAR_RE.search(t)
        if not m:
            return fallback_report_date

        year = int(m.group(1))
        if report_type == "annual":
            return f"{year}-12-31"
        if report_type == "semi":
            return f"{year}-06-30"
        if report_type == "q1":
            return f"{year}-03-31"
        if report_type == "q3":
            return f"{year}-09-30"
        return fallback_report_date

    @classmethod
    def is_valid_report_title(cls, title: str) -> bool:
        t = cls.strip_html(title)
        if not any(k in t for k in cls.INCLUDE_KEYWORDS):
            return False
        if any(k in t for k in cls.EXCLUDE_KEYWORDS):
            return False
        return True

    def _rate_limit_query(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last_query_ts
            wait_seconds = self.settings.query_rate_limit_seconds - elapsed
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            self._last_query_ts = time.monotonic()

    def _post_with_retry(self, data: Dict[str, str]) -> Dict[str, object]:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
        }

        last_error = None
        for attempt in range(self.settings.query_retries):
            try:
                self._rate_limit_query()
                resp = self.session.post(
                    self.settings.cninfo_query_url,
                    headers=headers,
                    data=data,
                    timeout=20,
                )
                resp.raise_for_status()
                payload = resp.json()
                if isinstance(payload, dict):
                    return payload
                last_error = RuntimeError("cninfo response is not an object")
            except Exception as exc:  # pragma: no cover - network instability path
                last_error = exc
                time.sleep(2 ** attempt)

        raise RuntimeError(f"cninfo query failed after retries: {last_error}")

    def _category_string(self, report_types: Sequence[str]) -> str:
        categories = [self.REPORT_CATEGORY_MAP[t] for t in report_types if t in self.REPORT_CATEGORY_MAP]
        if not categories:
            categories = [self.REPORT_CATEGORY_MAP[t] for t in ("annual", "semi", "q1", "q3")]
        return ";".join(categories)

    @staticmethod
    def _report_date_from_timestamp(ts_ms: object) -> str:
        try:
            ts = int(ts_ms) / 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        except Exception:
            return ""

    def query_announcements(
        self,
        code: str,
        name: Optional[str],
        years: int,
        report_types: Sequence[str],
        max_pages: int = 20,
    ) -> List[CninfoAnnouncement]:
        """Query cninfo and return filtered report announcements for one stock code."""
        column, plate, exchange_label = self.map_exchange(code)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365 * years)
        se_date = f"{start_date.isoformat()}~{end_date.isoformat()}"
        categories = self._category_string(report_types)

        # Name tends to be far more precise than numeric code search on cninfo.
        search_candidates = [s for s in (name, code) if s]

        unique: Dict[str, CninfoAnnouncement] = {}
        for keyword in search_candidates:
            for page in range(1, max_pages + 1):
                payload = {
                    "stock": "",
                    "tabName": "fulltext",
                    "pageSize": "30",
                    "pageNum": str(page),
                    "column": column,
                    "category": categories,
                    "plate": plate,
                    "seDate": se_date,
                    "searchkey": keyword,
                    "secid": "",
                    "sortName": "time",
                    "sortType": "desc",
                    "isHLtitle": "true",
                }

                response = self._post_with_retry(payload)
                rows = response.get("announcements") or []
                if not isinstance(rows, list) or not rows:
                    break

                accepted_in_page = 0
                for row in rows:
                    sec_code = str(row.get("secCode") or "").strip()
                    if sec_code != code:
                        continue

                    title = str(row.get("announcementTitle") or "")
                    if not self.is_valid_report_title(title):
                        continue

                    report_type = self.detect_report_type(title)
                    if not report_type:
                        continue
                    if report_type not in report_types:
                        continue

                    announcement_id = str(row.get("announcementId") or row.get("id") or "").strip()
                    adjunct_url = str(row.get("adjunctUrl") or "").strip()
                    if not announcement_id or not adjunct_url:
                        continue

                    report_date = self._report_date_from_timestamp(row.get("announcementTime"))
                    report_period = self.infer_report_period(title, report_type, report_date)
                    pdf_url = self.settings.cninfo_pdf_base_url + adjunct_url.lstrip("/")

                    unique[announcement_id] = CninfoAnnouncement(
                        code=code,
                        name=str(row.get("secName") or name or ""),
                        exchange=exchange_label,
                        announcement_id=announcement_id,
                        title=self.strip_html(title),
                        report_type=report_type,
                        report_date=report_date,
                        report_period=report_period,
                        pdf_url=pdf_url,
                        adjunct_url=adjunct_url,
                    )
                    accepted_in_page += 1

                # If a keyword no longer yields matched records, stop paging for that keyword.
                if accepted_in_page == 0 and page >= 2:
                    break

        records = list(unique.values())
        records.sort(key=lambda x: (x.report_date, x.announcement_id), reverse=True)
        return records

    def download_pdf(self, adjunct_url: str, output_path: Path) -> None:
        """Download one PDF file with retries."""
        url = self.settings.cninfo_pdf_base_url + adjunct_url.lstrip("/")
        headers = {"User-Agent": "Mozilla/5.0"}
        output_path.parent.mkdir(parents=True, exist_ok=True)

        last_error = None
        for attempt in range(self.settings.download_retries):
            try:
                with self.session.get(url, headers=headers, stream=True, timeout=60) as resp:
                    resp.raise_for_status()
                    with output_path.open("wb") as fh:
                        for chunk in resp.iter_content(chunk_size=1024 * 128):
                            if chunk:
                                fh.write(chunk)
                return
            except Exception as exc:  # pragma: no cover - network instability path
                last_error = exc
                time.sleep(2 ** attempt)

        raise RuntimeError(f"download failed: {url}, err={last_error}")
