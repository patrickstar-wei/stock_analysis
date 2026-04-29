from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

from app.clients.akshare_client import AkMetric, _to_float


_VENDOR_DIR = Path(__file__).resolve().parent.parent.parent / "_vendor"


class EfinanceClient:
    """Backup data source using efinance for latest-period metrics."""

    def __init__(self):
        self._ef = None
        try:
            if str(_VENDOR_DIR) not in sys.path:
                sys.path.insert(0, str(_VENDOR_DIR))
            import efinance as ef

            self._ef = ef
        except Exception:
            self._ef = None

    @property
    def available(self) -> bool:
        return self._ef is not None

    def get_latest_metrics(self, code: str) -> Tuple[Dict[str, AkMetric], str]:
        """Return latest-period metrics for a single stock."""
        if not self.available:
            return {}, "efinance_unavailable"

        metrics: Dict[str, AkMetric] = {}

        try:
            df = self._ef.stock.get_base_info([code])
            if df is not None and not df.empty:
                row = df.iloc[0]
                val = _to_float(row.get("净利润"))
                if val is not None:
                    metrics["归母净利润"] = AkMetric(value=val, unit="元")
                val = _to_float(row.get("ROE"))
                if val is not None:
                    metrics["ROE"] = AkMetric(value=val, unit="%")
                val = _to_float(row.get("毛利率"))
                if val is not None:
                    metrics["毛利率"] = AkMetric(value=val, unit="%")
        except Exception:
            pass

        try:
            df = self._ef.stock.get_all_company_performance()
            if df is not None and not df.empty:
                row = df[df["股票代码"].astype(str).str.zfill(6) == code]
                if not row.empty:
                    r = row.iloc[0]
                    val = _to_float(r.get("营业收入"))
                    if val is not None:
                        metrics["营业收入"] = AkMetric(value=val, unit="元")
                    val = _to_float(r.get("每股收益"))
                    if val is not None:
                        metrics["基本EPS"] = AkMetric(value=val, unit="元")
                    val = _to_float(r.get("净资产收益率"))
                    if val is not None and "ROE" not in metrics:
                        metrics["ROE"] = AkMetric(value=val, unit="%")
                    val = _to_float(r.get("销售毛利率"))
                    if val is not None and "毛利率" not in metrics:
                        metrics["毛利率"] = AkMetric(value=val, unit="%")
        except Exception:
            pass

        if not metrics:
            return {}, "efinance_empty"
        return metrics, "efinance_ok"
