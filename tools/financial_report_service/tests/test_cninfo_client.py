from app.clients.cninfo_client import CninfoClient


def test_map_exchange():
    assert CninfoClient.map_exchange("600519") == ("sse", "sh", "SSE")
    assert CninfoClient.map_exchange("000001") == ("szse", "sz", "SZSE")


def test_title_filter_and_type_detection():
    ok_title = "平安银行股份有限公司2024年年度报告"
    bad_title = "平安银行股份有限公司2024年年度报告摘要"

    assert CninfoClient.is_valid_report_title(ok_title) is True
    assert CninfoClient.is_valid_report_title(bad_title) is False
    assert CninfoClient.detect_report_type(ok_title) == "annual"


def test_infer_report_period():
    assert CninfoClient.infer_report_period("2025年第一季度报告", "q1", "2025-04-26") == "2025-03-31"
    assert CninfoClient.infer_report_period("2025年第三季度报告", "q3", "2025-10-30") == "2025-09-30"
