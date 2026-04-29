from app.services.extractor import MetricExtractor


def test_normalize_number_currency():
    m = MetricExtractor.normalize_number("1,234.5", "亿元", "营业收入")
    assert m is not None
    assert round(m.value, 2) == 123450000000.00
    assert m.unit == "元"


def test_normalize_number_percent():
    m = MetricExtractor.normalize_number("12.34", "%", "ROE")
    assert m is not None
    assert m.value == 12.34
    assert m.unit == "%"


def test_extract_from_text():
    text = "主要会计数据：营业收入 123.45亿元；归属于上市公司股东的净利润 10.2亿元；资产负债率 45.6%"
    ext = MetricExtractor()
    result = ext.extract_from_text(text)

    assert "营业收入" in result
    assert "归母净利润" in result
    assert "资产负债率" in result
