from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional

from app.models import MetricSource


METRIC_NAMES = [
    "营业收入",
    "营业成本",
    "归母净利润",
    "扣非净利润",
    "经营现金流净额",
    "基本EPS",
    "稀释EPS",
    "ROE",
    "总资产",
    "总负债",
    "归母权益",
    "资产负债率",
    "毛利率",
    "研发投入",
    "研发占比",
]

PERCENT_METRICS = {"ROE", "资产负债率", "毛利率", "研发占比"}


@dataclass(frozen=True)
class ExtractedMetric:
    value: float
    unit: str
    confidence: float


class MetricExtractor:
    # Metric aliases from common annual/interim report wording.
    METRIC_PATTERNS: Dict[str, tuple[str, ...]] = {
        "营业收入": (
            "营业收入",
            "营业总收入",
            "营业收入总额",
            "营业收入合计",
            "营业收入净额",
            "主营业务收入",
        ),
        "营业成本": (
            "营业成本",
            "营业总成本",
            "营业成本合计",
            "营业支出",
            "营业支出合计",
            "主营业务成本",
        ),
        "归母净利润": (
            "归属于上市公司股东的净利润",
            "归属于母公司股东的净利润",
            "归属于母公司所有者的净利润",
            "归属于母公司所有者净利润",
            "归属于本公司股东的净利润",
            "归属于本行股东的净利润",
            "归母净利润",
        ),
        "扣非净利润": (
            "归属于上市公司股东的扣除非经常性损益的净利润",
            "归属于母公司股东的扣除非经常性损益的净利润",
            "扣除非经常性损益后归属于上市公司股东的净利润",
            "扣除非经常性损益后归属于母公司股东的净利润",
            "扣除非经常性损益后归属于母公司所有者的净利润",
            "扣除非经常性损益后归属于本行股东的净利润",
            "扣除非经常性损益后归属于公司普通股股东的净利润",
            "扣非净利润",
        ),
        "经营现金流净额": (
            "经营活动产生的现金流量净额",
            "经营活动现金流量净额",
            "经营活动产生的现金净流量",
            "经营活动的现金流量净额",
        ),
        "基本EPS": (
            "基本每股收益",
        ),
        "稀释EPS": (
            "稀释每股收益",
        ),
        "ROE": (
            "净资产收益率",
            "加权平均净资产收益率",
            "加权净资产收益率",
            "全面摊薄净资产收益率",
        ),
        "总资产": (
            "总资产",
            "资产总额",
            "资产总计",
            "资产合计",
        ),
        "总负债": (
            "总负债",
            "负债合计",
            "负债总额",
            "负债总计",
        ),
        "归母权益": (
            "归属于上市公司股东的所有者权益",
            "归属于母公司股东权益",
            "归属于母公司所有者权益",
            "归属于母公司所有者权益合计",
            "归属于母公司股东权益合计",
            "归属于本公司股东的股东权益",
            "归属于本行普通股股东的股东权益",
            "归属于本行股东的股东权益",
            "股东权益合计",
            "股东权益",
        ),
        "资产负债率": (
            "资产负债率",
        ),
        "毛利率": (
            "销售毛利率",
            "毛利率",
            "综合毛利率",
            "主营业务毛利率",
        ),
        "研发投入": (
            "研发投入",
            "研发费用",
            "研发支出",
            "研发投入合计",
            "研发投入金额",
        ),
        "研发占比": (
            "研发投入占营业收入比例",
            "研发费用率",
            "研发投入占营业收入的比例",
            "研发投入比例",
            "研发支出占营业收入比例",
        ),
    }

    UNIT_SCALE = {"元": 1.0, "万元": 1e4, "亿元": 1e8, "百万元": 1e6, "千元": 1e3, "千万元": 1e7}

    VALUE_RE = re.compile(
        r"([\(（-]?\d[\d,]*\.?\d*[\)）]?)\s*(千万元|百万元|亿元|万元|千元|元|%)?",
        re.IGNORECASE,
    )

    @staticmethod
    def _clean_value(text: str) -> Optional[float]:
        if text is None:
            return None
        s = text.strip().replace(",", "")
        negative = False
        if s.startswith("(") or s.startswith("（"):
            negative = True
            s = s[1:]
        if s.endswith(")") or s.endswith("）"):
            s = s[:-1]
        if s.startswith("-"):
            negative = True
            s = s[1:]

        try:
            value = float(s)
        except ValueError:
            return None
        return -value if negative else value

    EPS_METRICS = {"基本EPS", "稀释EPS"}

    @classmethod
    def normalize_number(cls, raw: str, unit: Optional[str], metric_name: str) -> Optional[ExtractedMetric]:
        value = cls._clean_value(raw)
        if value is None:
            return None

        if unit in cls.UNIT_SCALE:
            if metric_name in cls.EPS_METRICS:
                return ExtractedMetric(value=value, unit="元", confidence=0.8)
            value = value * cls.UNIT_SCALE[unit]
            return ExtractedMetric(value=value, unit="元", confidence=0.9)

        if unit == "%" or metric_name in PERCENT_METRICS:
            return ExtractedMetric(value=value, unit="%", confidence=0.9 if unit == "%" else 0.8)

        if metric_name in cls.EPS_METRICS:
            return ExtractedMetric(value=value, unit="元", confidence=0.8)

        return ExtractedMetric(value=value, unit="元", confidence=0.75)

    EXCLUDE_SUFFIXES: Dict[str, tuple[str, ...]] = {
        "总资产": ("收益率", "利润率", "报酬率", "回报率", "减值损失", "、"),
        "总负债": ("率", "、"),
        "营业收入": ("率", "占比", "比例"),
        "营业成本": ("率",),
        "股东权益": ("率",),
    }

    def _extract_metric(self, text: str, metric_name: str, page_unit: Optional[str] = None) -> Optional[ExtractedMetric]:
        aliases = self.METRIC_PATTERNS.get(metric_name, ())
        exclude_suffixes = self.EXCLUDE_SUFFIXES.get(metric_name, ())
        sorted_aliases = sorted(aliases, key=len, reverse=True)
        for alias in sorted_aliases:
            pattern = re.compile(rf"{re.escape(alias)}[^\n\r\d]{{0,40}}([^\n\r]{{0,80}})")
            for match in pattern.finditer(text):
                after_alias = text[match.start() + len(alias):match.start() + len(alias) + 10]
                if any(s in after_alias for s in exclude_suffixes):
                    continue
                scope = match.group(1)
                vmatch = self.VALUE_RE.search(scope)
                if not vmatch:
                    continue
                raw_unit = vmatch.group(2) or page_unit
                metric = self.normalize_number(vmatch.group(1), raw_unit, metric_name)
                if metric is not None:
                    return metric

        if metric_name == "基本EPS":
            merged = re.compile(r"基本[/／]\s*稀释每股收益[^\n\r\d]{0,20}([^\n\r]{0,60})")
            for match in merged.finditer(text):
                scope = match.group(1)
                vmatch = self.VALUE_RE.search(scope)
                if not vmatch:
                    continue
                raw_unit = vmatch.group(2) or page_unit
                metric = self.normalize_number(vmatch.group(1), raw_unit, metric_name)
                if metric is not None:
                    return metric

        if metric_name == "稀释EPS":
            merged = re.compile(r"基本[/／]\s*稀释每股收益[^\n\r\d]{0,20}([^\n\r]{0,60})")
            for match in merged.finditer(text):
                scope = match.group(1)
                values = self.VALUE_RE.findall(scope)
                if len(values) >= 2:
                    raw_unit = values[1][1] or page_unit
                    metric = self.normalize_number(values[1][0], raw_unit, metric_name)
                    if metric is not None:
                        return metric

        return None

    PAGE_UNIT_RE = re.compile(
        r"(?:货币单位|单位|金额单位)[：:]\s*人民币?\s*(千万元|百万元|亿元|万元|千元|元)",
    )

    def _detect_page_unit(self, text: str) -> Optional[str]:
        m = self.PAGE_UNIT_RE.search(text)
        if m:
            return m.group(1)
        return None

    def extract_from_text(self, text: str) -> Dict[str, ExtractedMetric]:
        if not text:
            return {}

        compact = re.sub(r"\s+", " ", text)
        page_unit = self._detect_page_unit(compact)
        result: Dict[str, ExtractedMetric] = {}

        for metric_name in METRIC_NAMES:
            extracted = self._extract_metric(compact, metric_name, page_unit=page_unit)
            if extracted is not None:
                result[metric_name] = extracted

        return result

    @staticmethod
    def merge_metrics(
        pdf_metrics: Dict[str, ExtractedMetric],
        ak_metrics: Dict[str, object],
    ) -> Dict[str, Dict[str, object]]:
        """Merge metrics by priority: PDF > AkShare > missing."""
        merged: Dict[str, Dict[str, object]] = {}

        for metric_name in METRIC_NAMES:
            if metric_name in pdf_metrics:
                m = pdf_metrics[metric_name]
                merged[metric_name] = {
                    "value": m.value,
                    "unit": m.unit,
                    "source": MetricSource.pdf.value,
                    "confidence": m.confidence,
                }
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

            merged[metric_name] = {
                "value": None,
                "unit": "%" if metric_name in PERCENT_METRICS else "元",
                "source": MetricSource.missing.value,
                "confidence": 0.0,
            }

        return merged
