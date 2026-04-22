# services/pdf_parser.py
import pdfplumber
import re
from typing import List, Dict, Tuple, Optional


def parse_pdf(pdf_path: str) -> List[Dict]:
    """Parse PDF and return text per page with page numbers."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "page_num": i + 1,
                    "text": text.strip()
                })
    print(f"Parsed {len(pages)} pages")
    return pages


def detect_section(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Detect section and clause number from chunk text.
    e.g. '18.1 Minimum rates' -> (None, '18.1')
    e.g. 'Schedule B-Junior rates' -> ('Schedule B', None)
    """
    section = None
    clause = None

    schedule_match = re.match(r'^(Schedule\s+[A-Z][^\n]*)', text, re.IGNORECASE)
    if schedule_match:
        section = schedule_match.group(1).strip()

    clause_match = re.match(r'^(\d+\.\d+(?:\.\d+)?)', text)
    if clause_match:
        clause = clause_match.group(1)

    return section, clause