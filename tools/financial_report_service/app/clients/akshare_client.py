from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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


def _normalize_period(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return _normalize_date(text)


@dataclass(frozen=True)
class AkMetric:
    value: float
    unit: str


INCOME_COL_MAP: Dict[str, Tuple[str, str]] = {
    "营业收入": ("营业收入", "元"),
    "营业成本": ("营业成本", "元"),
    "归母净利润": ("归属于母公司所有者的净利润", "元"),
    "基本EPS": ("基本每股收益", "元"),
    "稀释EPS": ("稀释每股收益", "元"),
    "研发投入": ("研发费用", "元"),
}

BALANCE_COL_MAP: Dict[str, Tuple[str, str]] = {
    "总资产": ("资产总计", "元"),
    "总负债": ("负债合计", "元"),
    "归母权益": ("归属于母公司股东权益合计", "元"),
}

CASHFLOW_COL_MAP: Dict[str, Tuple[str, str]] = {
    "经营现金流净额": ("经营活动产生的现金流量净额", "元"),
}

ABSTRACT_ROW_MAP: Dict[str, Tuple[str, str]] = {
    "扣非净利润": ("扣非净利润", "元"),
    "ROE": ("净资产收益率(ROE)", "%"),
    "毛利率": ("毛利率", "%"),
    "资产负债率": ("资产负债率", "%"),
    "经营现金流净额": ("经营现金流量净额", "元"),
    "基本EPS": ("基本每股收益", "元"),
    "稀释EPS": ("稀释每股收益", "元"),
    "归母净利润": ("归母净利润", "元"),
    "营业收入": ("营业总收入", "元"),
    "营业成本": ("营业成本", "元"),
    "总资产": ("总资产报酬率(ROA)", "__skip__"),
    "归母权益": ("股东权益合计(净资产)", "元"),
}

PERCENT_METRICS = {"ROE", "资产负债率", "毛利率", "研发占比"}


class AkshareClient:
    """Best-effort wrapper around AkShare with graceful fallback."""

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

    def _fetch_income_statement(self, code: str) -> Dict[str, Dict[str, AkMetric]]:
        if not self.available:
            return {}
        try:
            df = self._ak.stock_financial_report_sina(stock=code, symbol="利润表")
        except Exception:
            return {}
        if df is None or df.empty:
            return {}
        return self._parse_statement_df(df, INCOME_COL_MAP)

    def _fetch_balance_sheet(self, code: str) -> Dict[str, Dict[str, AkMetric]]:
        if not self.available:
            return {}
        try:
            df = self._ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
        except Exception:
            return {}
        if df is None or df.empty:
            return {}
        return self._parse_statement_df(df, BALANCE_COL_MAP)

    def _fetch_cash_flow(self, code: str) -> Dict[str, Dict[str, AkMetric]]:
        if not self.available:
            return {}
        try:
            df = self._ak.stock_financial_report_sina(stock=code, symbol="现金流量表")
        except Exception:
            return {}
        if df is None or df.empty:
            return {}
        return self._parse_statement_df(df, CASHFLOW_COL_MAP)

    def _parse_statement_df(
        self, df: pd.DataFrame, col_map: Dict[str, Tuple[str, str]]
    ) -> Dict[str, Dict[str, AkMetric]]:
        result: Dict[str, Dict[str, AkMetric]] = {}
        date_col = "报告日"
        if date_col not in df.columns:
            return result

        for _, row in df.iterrows():
            period = _normalize_period(row.get(date_col))
            if not period:
                continue
            metrics: Dict[str, AkMetric] = {}
            for metric_name, (col_name, unit) in col_map.items():
                if col_name not in df.columns:
                    continue
                val = _to_float(row.get(col_name))
                if val is not None:
                    metrics[metric_name] = AkMetric(value=val, unit=unit)
            if metrics:
                if period not in result:
                    result[period] = {}
                result[period].update(metrics)
        return result

    def _fetch_abstract(self, code: str) -> Dict[str, Dict[str, AkMetric]]:
        if not self.available:
            return {}
        try:
            df = self._ak.stock_financial_abstract(symbol=code)
        except Exception:
            return {}
        if df is None or df.empty:
            return {}

        result: Dict[str, Dict[str, AkMetric]] = {}
        period_cols = [
            c for c in df.columns if re.match(r"^\d{8}$", str(c))
        ]

        for _, row in df.iterrows():
            indicator = str(row.get("指标", "")).strip()
            for metric_name, (row_name, unit) in ABSTRACT_ROW_MAP.items():
                if indicator != row_name:
                    continue
                if unit == "__skip__":
                    continue
                for col in period_cols:
                    period = _normalize_period(col)
                    if not period:
                        continue
                    val = _to_float(row.get(col))
                    if val is not None:
                        if period not in result:
                            result[period] = {}
                        result[period][metric_name] = AkMetric(value=val, unit=unit)
        return result

    @staticmethod
    def _compute_derived(period_metrics: Dict[str, Dict[str, AkMetric]]) -> None:
        for metrics in period_metrics.values():
            total_assets = metrics.get("总资产")
            total_liabilities = metrics.get("总负债")
            if (
                total_assets
                and total_liabilities
                and total_assets.value
                and total_liabilities.value
                and "资产负债率" not in metrics
            ):
                ratio = total_liabilities.value / total_assets.value
                metrics["资产负债率"] = AkMetric(value=ratio * 100, unit="%")

            revenue = metrics.get("营业收入")
            cost = metrics.get("营业成本")
            if (
                revenue
                and cost
                and revenue.value
                and cost.value
                and "毛利率" not in metrics
                and revenue.value != 0
            ):
                margin = (revenue.value - cost.value) / revenue.value
                metrics["毛利率"] = AkMetric(value=margin * 100, unit="%")

            rd = metrics.get("研发投入")
            if (
                revenue
                and rd
                and revenue.value
                and rd.value
                and "研发占比" not in metrics
                and revenue.value != 0
            ):
                ratio = rd.value / revenue.value
                metrics["研发占比"] = AkMetric(value=ratio * 100, unit="%")

    def get_financial_metrics_by_period(
        self, code: str
    ) -> Tuple[Dict[str, Dict[str, AkMetric]], str]:
        """Return period -> metric_name -> AkMetric using all available APIs."""
        if not self.available:
            return {}, "akshare_unavailable"

        merged: Dict[str, Dict[str, AkMetric]] = {}

        income = self._fetch_income_statement(code)
        self._merge_period_metrics(merged, income)

        balance = self._fetch_balance_sheet(code)
        self._merge_period_metrics(merged, balance)

        cashflow = self._fetch_cash_flow(code)
        self._merge_period_metrics(merged, cashflow)

        abstract = self._fetch_abstract(code)
        self._merge_period_metrics(merged, abstract)

        if not merged:
            try:
                df = self._ak.stock_financial_analysis_indicator(symbol=code)
                if df is not None and not df.empty:
                    fallback = self._extract_legacy_indicator(df)
                    self._merge_period_metrics(merged, fallback)
            except Exception:
                pass

        if not merged:
            return {}, "akshare_empty"

        self._compute_derived(merged)
        return merged, "akshare_ok"

    @staticmethod
    def _merge_period_metrics(
        target: Dict[str, Dict[str, AkMetric]],
        source: Dict[str, Dict[str, AkMetric]],
    ) -> None:
        for period, metrics in source.items():
            if period not in target:
                target[period] = {}
            for name, metric in metrics.items():
                if name not in target[period]:
                    target[period][name] = metric

    LEGACY_ALIASES: Dict[str, Tuple[Tuple[str, str], ...]] = {
        "营业收入": (
            ("营业收入", "元"),
            ("营业总收入", "元"),
        ),
        "营业成本": (
            ("营业成本", "元"),
            ("营业总成本", "元"),
        ),
        "归母净利润": (
            ("归属于母公司股东的净利润", "元"),
            ("净利润", "元"),
        ),
        "扣非净利润": (
            ("扣除非经常性损益后的净利润", "元"),
        ),
        "经营现金流净额": (
            ("经营活动产生的现金流量净额", "元"),
        ),
        "基本EPS": (("基本每股收益", "元"),),
        "稀释EPS": (("稀释每股收益", "元"),),
        "ROE": (
            ("净资产收益率", "%"),
            ("加权净资产收益率", "%"),
        ),
        "总资产": (("总资产", "元"), ("资产总计", "元")),
        "总负债": (("负债合计", "元"), ("总负债", "元")),
        "归母权益": (
            ("归属于母公司股东权益", "元"),
            ("股东权益合计", "元"),
        ),
        "资产负债率": (("资产负债率", "%"),),
        "毛利率": (("销售毛利率", "%"), ("毛利率", "%")),
        "研发投入": (("研发费用", "元"),),
        "研发占比": (("研发费用率", "%"),),
    }

    LEGACY_DATE_COLUMNS = ("日期", "报告期", "report_date", "trade_date")

    def _extract_legacy_indicator(
        self, df: pd.DataFrame
    ) -> Dict[str, Dict[str, AkMetric]]:
        result: Dict[str, Dict[str, AkMetric]] = {}
        date_col = None
        for candidate in self.LEGACY_DATE_COLUMNS:
            if candidate in df.columns:
                date_col = candidate
                break
        if date_col is None:
            latest = df.iloc[0]
            metrics = self._extract_metrics_from_row_legacy(latest)
            if metrics:
                result[""] = metrics
            return result

        for _, row in df.iterrows():
            period = _normalize_date(row.get(date_col))
            if not period:
                continue
            metrics = self._extract_metrics_from_row_legacy(row)
            if metrics:
                result[period] = metrics
        return result

    def _extract_metrics_from_row_legacy(
        self, row: pd.Series
    ) -> Dict[str, AkMetric]:
        out: Dict[str, AkMetric] = {}
        for metric_name, aliases in self.LEGACY_ALIASES.items():
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
