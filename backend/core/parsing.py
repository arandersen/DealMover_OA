import io
import re
from typing import Optional, Dict
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

_NUMBER_RE = re.compile(r'\(?\s*\$?\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*\)?')

# Labels (initial scope; variants deferred to live session)
_REVENUE_LABEL_RE = re.compile(r'\bRevenues?\b', re.IGNORECASE)
_COS_LABEL_RE     = re.compile(r'\bCost\s+of\s+Sales\b', re.IGNORECASE)

def _normalize_value(value: str) -> str:
    """
    Remove $, commas, spaces; convert '(123)' -> '-123'.
    Return numeric string without commas/spaces.
    """
    v = value.strip().replace('$', '').replace(',', '').replace(' ', '')
    if v.startswith('(') and v.endswith(')'):
        v = '-' + v[1:-1]
    return v

def _first_number_after_label(line: str, label_match: re.Match) -> Optional[str]:
    """
    Finds the first numeric token that appears AFTER the label on the same line.
    """
    start_idx = label_match.end()
    for m in _NUMBER_RE.finditer(line, pos=start_idx):
        return m.group(0)
    return None

def _first_number_in_line(line: str) -> Optional[str]:
    """
    Fallback: first numeric token anywhere in the line.
    """
    m = _NUMBER_RE.search(line)
    return m.group(0) if m else None

def extract_values_from_pdf(pdf_bytes: bytes) -> Dict[str, Optional[str]]:
    """
    Extract normalized 'revenue' and 'cos' from a text-based 10-K PDF.
    Heuristic:
      - take the FIRST number after the label on the same line;
      - if none, look ahead one line and take the first number there.
    """
    text = extract_text(io.BytesIO(pdf_bytes), laparams=LAParams()) or ""
    lines = [ln.strip() for ln in text.splitlines()]

    revenue: Optional[str] = None
    cos: Optional[str] = None

    i = 0
    while i < len(lines) and (revenue is None or cos is None):
        line = lines[i]

        if revenue is None:
            m = _REVENUE_LABEL_RE.search(line)
            if m:
                val = _first_number_after_label(line, m)
                if not val and i + 1 < len(lines):
                    val = _first_number_in_line(lines[i + 1])
                if val:
                    revenue = _normalize_value(val)

        if cos is None:
            m = _COS_LABEL_RE.search(line)
            if m:
                val = _first_number_after_label(line, m)
                if not val and i + 1 < len(lines):
                    val = _first_number_in_line(lines[i + 1])
                if val:
                    cos = _normalize_value(val)

        i += 1

    return {"revenue": revenue, "cos": cos}
