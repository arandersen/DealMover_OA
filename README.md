# DealMover Financial Data Extractor

A minimal full-stack app that extracts **Revenue** and **Cost of Sales/Revenue(s)** from a **text-based 10-K PDF**, **normalizes** them, computes **Gross Profit** on the **backend**, and displays **Revenue** + **Gross Profit** in a simple React grid.

## Features

- PDF upload with optional **period end date**
- Automated extraction of **Revenue** and **Cost of Sales/Revenue(s)**
- Strict **normalization** of figures (remove `$`, spaces/commas/periods; `(123)`→`-123`)
- **Gross Profit** calculated on the **backend** (`revenue - cos`)
- Clean UI with **loading & error handling**
- Vite dev **proxy** to avoid CORS during development

## Tech Stack

**Backend**

- Python 3.8+
- Django
- pdfminer.six (PDF text extraction)

**Frontend**

- Vite
- React
- TypeScript
- Modern CSS (flex/grid, lightweight inline styles)

---

## Quick Start

### 1) Backend

```bash
cd backend
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows (PowerShell):
# .\venv\Scripts\Activate.ps1

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver   # http://127.0.0.1:8000
```

Health check:

```bash
curl -i http://127.0.0.1:8000/api/health
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

> The Vite dev server proxies `/api/*` → `http://localhost:8000`.

---

## How to Use (End-to-End)

1. Open `http://localhost:5173`.
2. Choose a **text-based** 10-K PDF (not scanned/OCR).
3. (Optional) Enter a `period_end_date` (e.g., `2023-12-31`).
4. Click **Upload & Extract**.
5. You’ll see:

   - Statement period (echoed back)
   - A small grid with **Revenue** and **Gross Profit**

---

## API

### `POST /api/extract/`

**Request**

- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:

  - `file`: PDF (required)
  - `period_end_date`: `YYYY-MM-DD` (optional)

**Response (200)**

```json
{
  "period_end_date": "YYYY-MM-DD",
  "results": {
    "revenue": "1234567",
    "cos": "456789",
    "gross_profit": "777778"
  }
}
```

**Errors**

- `400` — Bad Request (missing file / non-PDF / unreadable upload)
- `422` — Unprocessable Entity (couldn’t extract `revenue` and/or `cos`)
- `500` — Internal Server Error (unexpected failure)

---

## Parsing Rules (current scope)

- **Labels**

  - Revenue: matches `\bRevenues?\b`
  - Cost of Sales/Revenue(s): matches `\bCost\s+of\s+(Sales|Revenue|Revenues)\b`

- **Numbers**

  - Accept `$`, commas, spaces, decimals, parentheses:

    - Examples: `$ 146,306`, `146 306`, `(123)`, `307 , 394`

  - **Normalization**: remove `$`, spaces, commas, periods; `(123)` → `-123`

- **Selection heuristic**

  1. On the **label line**, only consider **money-like** tokens:

     - Has `$`, or
     - Has ≥4 digits after normalization
     - Not a bare year (1900–2100)
     - If none → **skip** same-line selection

  2. **Look-ahead** (up to \~10–12 lines):

     - If any tokens contain `$` on a line, **pick the leftmost** `$` token (first column)
     - Otherwise, pick the **leftmost** token with ≥4 digits (not a year)

- **Computation**

  - `gross_profit = revenue - cos` using `Decimal` for numeric safety
  - Output numeric strings without separators or trailing zeros

---

## Development Notes

- **Dev proxy** (Vite) forwards `/api/*` to Django → no CORS setup needed in dev.
- Uploaded files are processed **in memory**; no persistence by default.
- The backend is the **single source of truth** for normalization and derived values.
- The UI performs **no arithmetic** (it displays backend results).

---

## Security & Validation

- Validate **file type** (must be PDF by content-type or extension)
- No file persistence beyond request processing
- Defensive parsing (skip bare years; prefer money-like tokens)
- Clear error messages and HTTP codes

---

## Project Structure

```
repo-root/
  README.md
  PRD.md
  AI_USAGE.md
  DECISIONS.md
  backend/
    manage.py
    project/
      settings.py
      urls.py
      ...
    core/
      parsing.py     # extraction + normalization + gross profit
      views.py       # /api/health, /api/extract/
      urls.py
      tests/         # (optional) pytest/unit tests
    requirements.txt
  frontend/
    vite.config.ts   # /api → http://localhost:8000
    src/
      api/
        client.ts    # typed fetch to /api/extract/
      components/
        ResultsGrid.tsx
      types.ts
      App.tsx
      main.tsx
    package.json
```

---

## Troubleshooting

- **404 at “/” on backend** — expected; only `/api/health` and `/api/extract/` exist.
- **“Unapplied migrations” warning** — run `python manage.py migrate`.
- **422 “Could not extract …”** — ensure:

  - PDF is **text-based** (selectable text)
  - The labels appear (e.g., “Revenues”, “Cost of revenues”)

- **Proxy not working** — confirm `frontend/vite.config.ts`:

  ```ts
  server: { proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } } }
  ```

---

## Future Improvements

1. Unit tests for parser (normalization, look-ahead, footnotes/years).
2. File size limits and additional validations.
3. Support for additional financial fields (e.g., Operating Income).
4. Rightmost/period-aware selection based on chosen `period_end_date`.
5. Basic data visualization or formatting (e.g., 1,234,567) in the UI.

---

## Why backend computes?

- **Consistency**: one place for normalization & formulas.
- **Minimal overhead**: subtraction is O(1); JSON adds only bytes.
- **Easier changes**: new derived fields or rounding rules don’t touch the UI.
