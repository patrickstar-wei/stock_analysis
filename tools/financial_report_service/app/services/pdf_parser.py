from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pdfplumber

from app.config import Settings


@dataclass
class PDFTextResult:
    text: str
    page_count: int
    char_count: int
    scanned_suspected: bool


class PDFParser:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _extract_with_pdfplumber(self, pdf_path: Path, max_pages: int) -> PDFTextResult:
        texts = []
        page_count = 0
        with pdfplumber.open(str(pdf_path)) as pdf:
            page_count = len(pdf.pages)
            limit = page_count if max_pages <= 0 else min(max_pages, page_count)
            for idx in range(limit):
                page_text = pdf.pages[idx].extract_text() or ""
                texts.append(page_text)

        full_text = "\n".join(texts)
        char_count = len(full_text.strip())
        return PDFTextResult(
            text=full_text,
            page_count=page_count,
            char_count=char_count,
            scanned_suspected=char_count < self.settings.scanned_text_threshold,
        )

    def _extract_with_pdftotext(self, pdf_path: Path, max_pages: int) -> Optional[PDFTextResult]:
        if shutil.which("pdftotext") is None:
            return None

        cmd = ["pdftotext", str(pdf_path), "-"]
        if max_pages > 0:
            cmd = ["pdftotext", "-f", "1", "-l", str(max_pages), str(pdf_path), "-"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except Exception:
            return None

        text = proc.stdout or ""
        char_count = len(text.strip())
        return PDFTextResult(
            text=text,
            page_count=max_pages if max_pages > 0 else char_count // 2000,
            char_count=char_count,
            scanned_suspected=char_count < self.settings.scanned_text_threshold,
        )

    def extract_text(self, pdf_path: Path, max_pages: int = 0) -> PDFTextResult:
        result = self._extract_with_pdfplumber(pdf_path, max_pages=max_pages)
        if result.char_count > 0:
            return result

        fallback = self._extract_with_pdftotext(pdf_path, max_pages=max_pages)
        if fallback:
            return fallback

        return result
