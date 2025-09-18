import io
import re
from typing import Optional, Dict
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from decimal import Decimal, InvalidOperation

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

def compute_gross_profit(revenue_str: str, cos_str: str) -> str:
    """
    Compute gross_profit = revenue - cos.
    Inputs are normalized numeric strings (may include a leading '-'
    and/or a decimal point). Returns a numeric string with no commas
    or trailing zeros. Raises ValueError for missing/invalid inputs.
    """
    if revenue_str is None or cos_str is None:
        raise ValueError("Missing revenue or cost of sales value.")

    try:
        rev = Decimal(revenue_str)
        cos = Decimal(cos_str)
    except InvalidOperation as e:
        raise ValueError("Invalid numeric input for revenue or cost of sales.") from e

    gp = rev - cos

    # Format as a plain string (no scientific notation), strip trailing zeros.
    s = format(gp.normalize(), 'f')  # e.g., '203712.000' -> '203712'
    if '.' in s:
        s = s.rstrip('0').rstrip('.')

    # Avoid '-0' edge case
    if s in ('-0', '-0.0', '0.0'):
        s = '0'

    return s
