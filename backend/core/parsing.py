import io
import re
from typing import Optional, Dict, List
from decimal import Decimal, InvalidOperation
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

# Accept amounts like "146,306", "146 306", "307 , 394", with optional $ and parentheses.
_NUMBER_RE = re.compile(
    r'\(?\s*\$?\s*\d{1,3}(?:\s*[,\.\s]\s*\d{3})*(?:\.\d+)?\s*\)?'
)

# Labels (initial scope; variants deferred to live session except COS broadened)
_REVENUE_LABEL_RE = re.compile(r'\bRevenues?\b', re.IGNORECASE)
_COS_LABEL_RE     = re.compile(r'\bCost\s+of\s+(Sales|Revenue|Revenues)\b', re.IGNORECASE)


def _normalize_value(value: str) -> str:
    """Remove $, commas, spaces, periods; convert '(123)' -> '-123'."""
    v = value.strip().replace('$', '').replace(',', '').replace(' ', '').replace('.', '')
    if v.startswith('(') and v.endswith(')'):
        v = '-' + v[1:-1]
    return v


def _looks_like_year(token: str) -> bool:
    """Treat a bare 4-digit 1900–2100 token as a year (avoid grabbing headers)."""
    t = token.strip().replace('$', '').replace(',', '').replace(' ', '').replace('.', '')
    return len(t) == 4 and t.isdigit() and 1900 <= int(t) <= 2100


def _money_like_tokens(tokens: List[str]) -> List[str]:
    """
    Keep tokens that look like money: has $, has grouping chars, or ≥4 digits
    after normalization. If nothing qualifies, fall back to originals.
    """
    good: List[str] = []
    for raw in tokens:
        norm = raw.strip().replace('$', '').replace(',', '').replace(' ', '').replace('.', '')
        has_group = (',' in raw) or (' ' in raw) or ('.' in raw)
        if ('$' in raw) or has_group or (norm.isdigit() and len(norm) >= 4):
            good.append(raw)
    return good or tokens


def _score_token(raw: str) -> int:
    """Higher score = more likely a money amount."""
    has_dollar = '$' in raw
    has_paren  = '(' in raw and ')' in raw
    has_group  = (',' in raw) or (' ' in raw) or ('.' in raw)
    norm = raw.strip().replace('$', '').replace(',', '').replace(' ', '').replace('.', '')
    is_year = _looks_like_year(raw)

    score = 0
    if has_dollar: score += 4
    if has_group:  score += 3
    if len(norm) >= 6: score += 3
    elif len(norm) >= 4: score += 2
    else: score -= 2  # penalize tiny tokens like "202" or "(1)"
    if has_paren: score += 1
    if is_year and not has_dollar: score -= 5
    return score


def _pick_best(candidates: List[str]) -> Optional[str]:
    """Score candidates; on tie, prefer the later token on the line (current period bias)."""
    if not candidates:
        return None
    candidates = _money_like_tokens(candidates)
    best_idx = -1
    best_score = -10**9
    for idx, c in enumerate(candidates):
        s = _score_token(c)
        if s > best_score or (s == best_score and idx > best_idx):
            best_score, best_idx = s, idx
    return candidates[best_idx]


def _best_number_after_label(line: str, label_match: re.Match) -> Optional[str]:
    """
    Choose the best numeric token AFTER the label on the same line.
    Only consider tokens that look like money (has $ OR >=4 digits after normalize)
    and are not bare years. If none qualify, return None so we fall back to look-ahead.
    """
    start_idx = label_match.end()
    raw = [m.group(0) for m in _NUMBER_RE.finditer(line, pos=start_idx)]
    if not raw:
        return None

    # Keep tokens that look like money
    candidates: List[str] = []
    for t in raw:
        norm = t.strip().replace('$', '').replace(',', '').replace(' ', '').replace('.', '').replace('(', '').replace(')', '')
        money_like = ('$' in t) or (norm.isdigit() and len(norm) >= 4)
        if money_like and not _looks_like_year(t):
            candidates.append(t)

    if not candidates:
        return None  # force look-ahead to find the actual amount line

    return _pick_best(candidates)

def _pick_leftmost(candidates: List[str]) -> Optional[str]:
    """Pick the leftmost candidate (index 0) after prior filtering."""
    return candidates[0] if candidates else None


def _best_number_in_next_lines(lines: List[str], start_idx: int, window: int = 10) -> Optional[str]:
    """
    Look forward up to `window` lines for the first money-like token.
    Priority per line:
      1) If any tokens contain '$', consider ONLY those and pick the LEFTMOST.
      2) Else consider tokens with >= 4 digits after normalization (and not a year) and pick the LEFTMOST.
      3) Else continue to next line.
    Returns the RAW token string (caller will normalize).
    """
    for j in range(1, window + 1):
        i = start_idx + j
        if i >= len(lines):
            break
        line = lines[i].strip()
        if not line:
            continue

        raw_tokens = [m.group(0) for m in _NUMBER_RE.finditer(line)]
        if not raw_tokens:
            continue

        # Case 1: prefer tokens that include a dollar sign on this line
        dollar_tokens = [t for t in raw_tokens if '$' in t]
        if dollar_tokens:
            return _pick_leftmost(dollar_tokens)

        # Case 2: otherwise require >=4 digits after normalization and not a bare year
        long_tokens: List[str] = []
        for t in raw_tokens:
            norm = t.strip().replace('$', '').replace(',', '').replace(' ', '').replace('.', '').replace('(', '').replace(')', '')
            if norm.isdigit() and len(norm) >= 4 and not _looks_like_year(t):
                long_tokens.append(t)

        if long_tokens:
            return _pick_leftmost(long_tokens)

    return None



def extract_values_from_pdf(pdf_bytes: bytes) -> Dict[str, Optional[str]]:
    """
    Extract normalized 'revenue' and 'cos' from a text-based 10-K PDF.
    Heuristic:
      - choose the BEST number after the label on the same line;
      - if none, scan ahead up to 10 lines and pick the first money-like token.
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
                val = _best_number_after_label(line, m)
                if not val:
                    val = _best_number_in_next_lines(lines, i, window=10)
                if val:
                    revenue = _normalize_value(val)

        if cos is None:
            m = _COS_LABEL_RE.search(line)
            if m:
                val = _best_number_after_label(line, m)
                if not val:
                    val = _best_number_in_next_lines(lines, i, window=12)
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
    s = format(gp.normalize(), 'f')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    if s in ('-0', '-0.0', '0.0'):
        s = '0'
    return s
