from pathlib import Path

from app.services.storage import should_skip_report


def test_should_skip_report(tmp_path: Path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.7")

    index = {
        "a1": {"pdf_path": str(pdf)},
        "a2": {"pdf_path": str(tmp_path / "missing.pdf")},
    }

    assert should_skip_report(index, "a1", full_refresh=False) is True
    assert should_skip_report(index, "a2", full_refresh=False) is False
    assert should_skip_report(index, "a1", full_refresh=True) is False
