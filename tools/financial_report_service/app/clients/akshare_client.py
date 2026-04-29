from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

import pandas as pd


def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return None
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    text = text.replace("%", "")
    text = text.replace("倍", "")
    text = text.replace("(", "-").replace(")", "")
    text = text.replace("（", "-").replace("）", "")
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_date(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            continue

    m = re.search(r"(20\d{2})[-/年]?(\d{1,2})[-/月]?(\d{1,2})", text)
    if m:
        y, mo, d = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return datetime(y, mo, d).date().isoformat()
    return None


@dataclass(frozen=True)
class AkMetric:
    value: float
    unit: str


class AkshareClient:
    """Best-effort wrapper around AkShare with graceful fallback."""

    METRIC_ALIASES: Dict[str, Tuple[Tuple[str, str], ...]] = {
        "营业收入": (
            ("营业收入", "元"),
            ("营业总收入", "元"),
            ("营业收入总额", "元"),
            ("营业收入合计", "元"),
            ("主营业务收入", "元"),
        ),
        "营业成本": (
            ("营业成本", "元"),
            ("营业总成本", "元"),
            ("营业成本合计", "元"),
            ("营业支出", "元"),
            ("营业支出合计", "元"),
            ("主营业务成本", "元"),
        ),
        "归母净利润": (
            ("归属于母公司股东的净利润", "元"),
            ("归属于母公司所有者的净利润", "元"),
            ("归属于上市公司股东的净利润", "元"),
            ("归属于本行股东的净利润", "元"),
            ("净利润", "元"),
        ),
        "扣非净利润": (
            ("扣除非经常性损益后的净利润", "元"),
            ("扣除非经常性损益后归属于母公司股东的净利润", "元"),
            ("扣除非经常性损益后归属于上市公司股东的净利润", "元"),
            ("扣除非经常性损益后归属于母公司所有者的净利润", "元"),
        ),
        "经营现金流净额": (
            ("经营活动产生的现金流量净额", "元"),
            ("经营活动现金流量净额", "元"),
        ),
        "基本EPS": (
            ("基本每股收益", "元"),
        ),
        "稀释EPS": (
            ("稀释每股收益", "元"),
        ),
        "ROE": (
            ("净资产收益率", "%"),
            ("加权净资产收益率", "%"),
            ("加权平均净资产收益率", "%"),
            ("全面摊薄净资产收益率", "%"),
        ),
        "总资产": (
            ("总资产", "元"),
            ("资产总额", "元"),
            ("资产总计", "元"),
        ),
        "总负债": (
            ("负债合计", "元"),
            ("总负债", "元"),
            ("负债总额", "元"),
            ("负债总计", "元"),
        ),
        "归母权益": (
            ("归属于母公司股东权益", "元"),
            ("归属于母公司所有者权益", "元"),
            ("归属于母公司所有者权益合计", "元"),
            ("归属于母公司股东权益合计", "元"),
            ("股东权益合计", "元"),
        ),
        "资产负债率": (
            ("资产负债率", "%"),
        ),
        "毛利率": (
            ("销售毛利率", "%"),
            ("毛利率", "%"),
            ("综合毛利率", "%"),
        ),
        "研发投入": (
            ("研发费用", "元"),
            ("研发支出", "元"),
            ("研发投入", "元"),
        ),
        "研发占比": (
            ("研发费用率", "%"),
            ("研发投入占营业收入比例", "%"),
            ("研发支出占营业收入比例", "%"),
        ),
    }

    DATE_COLUMNS = ("日期", "报告期", "report_date", "trade_date")

    def __init__(self):
        self._ak = None
        self._stock_name_cache: Dict[str, str] = {}
        try:
            import akshare as ak

            self._ak = ak
        except Exception:
            self._ak = None

    @property
    def available(self) -> bool:
        return self._ak is not None

    def lookup_stock_name(self, code: str) -> str:
        if code in self._stock_name_cache:
            return self._stock_name_cache[code]
        if not self.available:
            return ""

        try:
            df = self._ak.stock_info_a_code_name()
            if df is not None and not df.empty:
                row = df[df["code"].astype(str).str.zfill(6) == code]
                if not row.empty:
                    name = str(row.iloc[0]["name"])
                    self._stock_name_cache[code] = name
                    return name
        except Exception:
            return ""
        return ""

    def _extract_metrics_from_row(self, row: pd.Series) -> Dict[str, AkMetric]:
        out: Dict[str, AkMetric] = {}

        for metric_name, aliases in self.METRIC_ALIASES.items():
            value = None
            unit = ""
            for alias, alias_unit in aliases:
                candidates = [col for col in row.index if alias in str(col)]
                for col in candidates:
                    parsed = _to_float(row[col])
                    if parsed is not None:
                        value = parsed
                        unit = alias_unit
                        break
                if value is not None:
                    break

            if value is None:
                continue
            out[metric_name] = AkMetric(value=value, unit=unit)
        return out

    def get_financial_metrics_by_period(self, code: str) -> Tuple[Dict[str, Dict[str, AkMetric]], str]:
        """Return period -> metric_name -> AkMetric."""
        if not self.available:
            return {}, "akshare_unavailable"

        try:
            df = self._ak.stock_financial_analysis_indicator(symbol=code)
        except Exception as exc:
            return {}, f"akshare_error:{exc}"

        if df is None or df.empty:
            return {}, "akshare_empty"

        date_col = None
        for candidate in self.DATE_COLUMNS:
            if candidate in df.columns:
                date_col = candidate
                break

        if date_col is None:
            # Use latest row as unknown period fallback.
            latest = df.iloc[0]
            return {"": self._extract_metrics_from_row(latest)}, "akshare_ok"

        result: Dict[str, Dict[str, AkMetric]] = {}
        for _, row in df.iterrows():
            period = _normalize_date(row.get(date_col))
            if not period:
                continue
            metrics = self._extract_metrics_from_row(row)
            if metrics:
                result[period] = metrics

        if not result:
            return {}, "akshare_no_metrics"
        return result, "akshare_ok"
