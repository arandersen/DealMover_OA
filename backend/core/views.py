from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .parsing import extract_values_from_pdf, compute_gross_profit

def health(request):
    return JsonResponse({"status": "ok"})

def _json_error(message: str, status: int):
    return JsonResponse({"error": message}, status=status)

@csrf_exempt                 # Simplifies dev; safe since this is a local OA.
@require_POST
def extract_view(request):
    """
    POST /api/extract/
    Form-data:
      - file: PDF (required)
      - period_end_date: YYYY-MM-DD (optional)
    Response:
      {
        "period_end_date": "YYYY-MM-DD" | null,
        "results": {
          "revenue": "<string>",
          "cos": "<string>",
          "gross_profit": "<string>"
        }
      }
    """
    file = request.FILES.get("file")
    if not file:
        return _json_error("Missing 'file' (PDF) in form-data.", 400)

    # Basic content-type/extension guard (not bulletproof, but OK for OA)
    ct = (file.content_type or "").lower()
    name = (getattr(file, "name", "") or "").lower()
    if "pdf" not in ct and not name.endswith(".pdf"):
        return _json_error("Uploaded file must be a PDF.", 400)

    # Optional date; echo back as provided (or null)
    period_end_date = request.POST.get("period_end_date") or None

    try:
        pdf_bytes = file.read()
    except Exception:
        return _json_error("Failed to read uploaded file.", 400)

    # Parse values
    try:
        vals = extract_values_from_pdf(pdf_bytes)  # {"revenue": str|None, "cos": str|None}
    except Exception:
        return _json_error("Failed to extract text from PDF.", 500)

    revenue = vals.get("revenue")
    cos = vals.get("cos")

    # If either missing, return 422 with a hint
    missing = [k for k, v in (("revenue", revenue), ("cos", cos)) if v is None]
    if missing:
        return _json_error(f"Could not extract: {', '.join(missing)}", 422)

    # Compute gross profit
    try:
        gross_profit = compute_gross_profit(revenue, cos)
    except ValueError as e:
        return _json_error(str(e), 422)
    except Exception:
        return _json_error("Failed to compute gross profit.", 500)

    data = {
        "period_end_date": period_end_date,
        "results": {
            "revenue": revenue,
            "cos": cos,
            "gross_profit": gross_profit,
        },
    }
    return JsonResponse(data, status=200)
