# Architectural Decisions

This document records the key decisions, assumptions, and trade-offs for the **DealMover Financial Data Extractor**. It also logs clarifications to the initial case-study requirements.

## 1) Backend Decisions

### 1.1 Framework: Django

* **Decision:** Use Django for the backend API.
* **Rationale:** Strong request/response model, file handling, mature security defaults, easy URL routing, quick local dev.

### 1.2 PDF Text Extraction: `pdfminer.six`

* **Decision:** Use `pdfminer.six` to extract text from PDFs.
* **Rationale:** Reliable text extraction for text-based 10-Ks; good handling of odd spacing/line breaks.

### 1.3 In-Memory File Processing

* **Decision:** Process uploads in memory; do not persist.
* **Rationale:** Simpler, less risk for sensitive documents, no cleanup cron.

### 1.4 Business Logic on Backend

* **Decision:** Perform **all** normalization and derived calculations (gross profit) on the backend.
* **Rationale:** Single source of truth; avoids logic duplication across clients; negligible performance impact.

### 1.5 API Contract

* **Endpoint:** `POST /api/extract/`
* **Request:** `multipart/form-data` with `file` (PDF, required) and `period_end_date` (optional `YYYY-MM-DD`).
* **Response (200):**

  ```json
  {
    "period_end_date": "YYYY-MM-DD" | null,
    "results": {
      "revenue": "<string, normalized>",
      "cos": "<string, normalized>",
      "gross_profit": "<string, normalized>"
    }
  }
  ```
* **Errors:** `400` (bad upload), `422` (missing extracted fields), `500` (unexpected).

### 1.6 Normalization Rules

* Remove **`$`**, **commas**, **spaces**, and **periods** used as thousands separators.
* Convert parentheses to negative: `(123)` → `-123`.
* Return **plain numeric strings** (no separators, no trailing zeros like `.000`).

### 1.7 Extraction Heuristic (Initial Scope)

* **Labels (narrow by design for v1):**

  * Revenue: `\bRevenues?\b`
  * Cost of Sales/Revenue(s): `\bCost\s+of\s+(Sales|Revenue|Revenues)\b`
* **Selection (Rule A with guarded look-ahead):**

  1. **Same line after label:** consider only **money-like** tokens (has `$` or ≥4 digits after normalization) and **not** bare years (1900–2100). If none → **skip** same-line selection.
  2. **Look-ahead window** (≈10–12 lines):

     * If a line has any **`$` tokens**, **pick the leftmost** (first column/older period).
     * Otherwise, pick the **leftmost** token with ≥4 digits (not a year).
* **Why:** Real 10-Ks often render amounts on subsequent lines, sometimes with footnotes or years on the label line. This rule avoids grabbing fragments like `202` or `(1)`.

### 1.8 Period/Column Choice

* **Decision:** When multiple columns are present on the value line, choose the **leftmost** amount during look-ahead.
* **Rationale:** Matches the provided example where the user passed `period_end_date=2023-12-31` and the leftmost column corresponded to that period. (A rightmost/current-year preference can be added later if required.)

### 1.9 Numeric Safety

* **Decision:** Use `Decimal` for `gross_profit = revenue − cos`.
* **Rationale:** Avoid float rounding issues; return clean string values.

### 1.10 Error Semantics

* **400 Bad Request:** Missing file; wrong type; unreadable payload.
* **422 Unprocessable Entity:** Couldn’t extract one or both target fields (`revenue`, `cos`).
* **500 Internal Server Error:** Unexpected exceptions.

---

## 2) Frontend Decisions

### 2.1 Vite + React + TypeScript

* **Decision:** Scaffold with Vite (`react-ts`).
* **Rationale:** Fast HMR, typed API client, light footprint.

### 2.2 Dev Proxy (Same-Origin UX)

* **Decision:** Vite `server.proxy['/api'] → http://localhost:8000`.
* **Rationale:** Avoid CORS, keep clean `/api/*` paths in client code.

### 2.3 Component Architecture

* **Decision:**

  * `App.tsx` → file/date form, fetch orchestration, loading/errors.
  * `ResultsGrid.tsx` → presentational table for **Revenue** and **Gross Profit**.
* **Rationale:** Clear separation of concerns; easy to extend.

### 2.4 Client State & Types

* **Decision:** `useState` for local state; `types.ts` for the API response shape.
* **Rationale:** Scope is small; no need for global state managers.

### 2.5 No UI-side Math

* **Decision:** The UI displays what the backend returns (no client math).
* **Rationale:** Keeps logic centralized; reduces edge-case drift.

---

## 3) Security & Validation

* Validate that the upload is a **PDF** (content-type or extension check).
* No file persistence beyond processing.
* Defensive parsing:

  * Skip **bare years** (1900–2100) unless prefixed with `$`.
  * Prefer **money-like tokens** and **`$` tokens** in look-ahead.
* Clear, minimal error messages for the client to surface.

---

## 4) Developer Experience

* **Health endpoint:** `GET /api/health` for quick sanity checks.
* **Unapplied migrations warning:** migrations are applied once at setup.
* **Repo layout:**

  ```
  backend/ (Django project & core app)
  frontend/ (Vite React TS)
  README.md / PRD.md / DECISIONS.md / AI_USAGE.md
  ```
* **Running locally:** Vite on 5173, Django on 8000, proxying `/api`.

---

## 5) Alternatives Considered (but not chosen)

* **OCR / scanned PDFs:** Out of scope; inputs are text-based.
* **Rightmost/current-period selection:** Possible enhancement; leftmost matches our test case and keeps rules simple.
* **CORS in dev:** Higher config complexity vs. simple proxy.
* **Persisting uploads:** Not required for the OA; increases risk/complexity.

---

## 6) Future Considerations

1. **Parsing robustness**

   * Add label variants: *Total Revenues*, *Consolidated Revenues*, *Net Sales*, etc. (live session).
   * Period-aware column picking (e.g., map `period_end_date` → target column).
   * Unit tests for formatting quirks (footnotes, multi-line blocks, negative values).

2. **Security & Scale**

   * File size limits; rate limiting; auth if multi-tenant.
   * Background workers for heavy PDFs; caching for repeat docs.

3. **Features**

   * Additional metrics (e.g., Operating Income).
   * Optional formatting of numbers in UI (e.g., `1,234,567`).
   * Batch processing and simple export (CSV/JSON).

---

## 7) Decision Log (TL;DR)

* **Compute on backend** (gross profit, normalization).
* **Narrow labels now; variants later** (live session).
* **Text-based PDFs** only (no OCR).
* **Vite + TS** frontend, **dev proxy** for same-origin `/api`.
* **Heuristic:** same-line money-like token or look-ahead to first `$` line (leftmost); skip years; normalize strictly.
* **Errors:** 400/422/500 with concise messages.

