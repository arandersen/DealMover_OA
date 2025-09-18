# PRD.md — DealMover Intern Case Study (Backend → Frontend)

## 0) Context & Decisions (from prompt + case docs)

* **Input:** text-based 10-K PDF (not scanned).
* **Compute:** All computations on **backend** (including `gross_profit = revenue - cos`).
* **Frontend:** Vite + TypeScript, follow example structure.
* **Label variants:** Defer to live session (initial parser targets the labels we implement now).
* **Dev setup:** Same-origin via **Vite dev proxy** (recommended for OA).

---

## 1) Problem Statement

Build a minimal system that:

1. Accepts a **10-K PDF upload** (+ optional `period_end_date`),
2. **Extracts:** Revenue and Cost of Sales (COS),
3. **Normalizes** values (remove \$/spaces; `(X) → -X`),
4. **Computes Gross Profit** on the backend, and
5. **Returns JSON** for a tiny React UI that displays a spreadsheet-like grid.

---

## 2) Goals / Non-Goals

### Goals

* Reliable extraction of **Revenue** and **Cost of Sales** from text-based PDFs.
* Deterministic **normalization**; **no hidden UI math**.
* Clean **API contract** + simple React **upload/display** flow.
* Clear **repo layout** + **run instructions**.

### Non-Goals

* **OCR** for scanned PDFs.
* Handling **many label variants** (saved for live extension).
* Styling beyond **basic readability**.

---

## 3) Functional Requirements

### 3.1 Backend (Django)

**Endpoint:** `POST /api/extract/`

**Request (multipart/form-data):**

* `file`: **required**, PDF
* `period_end_date`: optional, `YYYY-MM-DD` string

**Extraction targets:**

* `revenue`
* `cos` (Cost of Sales / Cost of Goods Sold—use whichever exact label we implement now)

**Normalization rules:**

* Remove `$` and **all spaces** from numbers.
* Convert parentheses to negative: `(123)` → `-123`.
* Return **numeric strings** (no commas).

**Computation (backend):**

* `gross_profit = revenue - cos` (use normalized numeric values)

**Response (JSON):**

```json
{
  "period_end_date": "2024-12-31",
  "results": {
    "revenue": "350018",
    "cos": "146306",
    "gross_profit": "203712"
  }
}
```

**Errors:**

* **400** — Missing file → message.
* **400** — Non-PDF.
* **422** — Extraction failure → which field failed.
* **500** — Generic server error.

---

### 3.2 Frontend (Vite + TS React)

* UI to **select PDF** + input optional **period end date**.
* Submit to `/api/extract/` and display:

**Grid with two rows:**

* Revenue
* Gross Profit

> **No UI-side arithmetic.**
> Show basic **loading** + **error** states.

---

## 4) Non-Functional Requirements

* **Performance:** Single PDF under \~15 MB; response **< 3s** on normal 10-K.
* **Security:** Accept only `application/pdf`; **no file persistence** beyond processing (temp storage OK).
* **Reliability:** Deterministic parsing; explicit **error messages**.
* **DX:** One-command per app to run; simple **proxy for same-origin**.

---

## 5) Interfaces & Contracts

### 5.1 HTTP API

**POST** `/api/extract/`
**Headers:** `Content-Type: multipart/form-data`

**Body:**

* `file` (PDF)
* `period_end_date` (optional)

**200 OK** → Body: JSON (schema above)

**4xx/5xx** → Body:

```json
{ "error": "human-readable message" }
```

### 5.2 Frontend contract

* Send **FormData** exactly as specified.
* Expect **JSON**; **no math in UI**.
* Render table:

| Metric       | Value  |
| ------------ | ------ |
| Revenue      | 350018 |
| Gross Profit | 203712 |

Optional: show `period_end_date` as a small header/caption.

---

## 6) Architecture & Repo Layout

```
repo-root/
  README.md
  PRD.md
  AI_USAGE.md
  DECISIONS.md
  /backend
    manage.py
    requirements.txt
    /project               # django project
    /core                  # app with views, urls, parser
      views.py
      urls.py
      parsing.py
      tests/               # pytest tests (optional)
  /frontend
    index.html
    vite.config.ts         # dev proxy → http://localhost:8000
    package.json
    /src
      main.tsx
      App.tsx
      components/ResultsGrid.tsx
      api/client.ts        # fetch wrapper
      types.ts
```

**Dev proxy (`vite.config.ts`):** Proxy `/api` → `http://localhost:8000`.

```ts
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

---

## 7) Implementation Plan (Tasks for AI agent)

### Phase A — Backend

**A1. Scaffold Django project**

* Create `/backend` project + `core` app.
* Add `django-cors-headers` **only if needed later** (not for proxy path).
* `requirements.txt` minimal: `Django`, `pdfminer.six` (or similar), `pytest` (optional).
* **Acceptance:** `python manage.py runserver` boots; `/api/health` returns 200.

**A2. Parsing utility**

* File: `core/parsing.py`
* Function: `extract_values_from_pdf(file_bytes) -> dict`
* Convert PDF → text.
* Find **Revenue** value.
* Find **Cost of Sales** value.
* Normalize per rules.
* Return `{ "revenue": "…", "cos": "…" }`
* Keep regexes/constants **scoped** for later label-variant extension.
* **Acceptance:** Unit test (if added) passes with a small fixture text.

**A3. Gross profit computation**

* Helper: `compute_gross_profit(revenue_str, cos_str) -> str`
* Safe string→int (handle `-`), compute, return string.
* **Acceptance:** Unit tests for sign/parentheses cases (e.g., `(123)`).

**A4. API endpoint**

* `core/views.py`: `POST /api/extract/`
* Validate PDF, optional `period_end_date`.
* Call parser, compute `gross_profit`.
* Return response JSON (exact schema).
* **Acceptance:** `curl` or Postman returns expected JSON for a sample file.

**A5. Error handling**

* **400:** missing/invalid file.
* **422:** revenue or cos not found (message specifies which).
* **500:** catch-all with safe message + server log.
* **Acceptance:** Negative tests return correct status/messages.

**A6. Docs**

* `README.md`: backend setup + run.
* `DECISIONS.md`: why backend computes values; why same-origin proxy.
* `AI_USAGE.md`: tools/prompts (if used).

---

### Phase B — Frontend

**B1. Scaffold Vite + TS**

* Create `/frontend` with Vite React + TS template.
* **Acceptance:** `npm run dev` serves the app.

**B2. Dev proxy**

* In `vite.config.ts`, proxy `/api` → `http://localhost:8000`.
* **Acceptance:** Frontend can hit backend **without CORS** errors.

**B3. API client**

* `src/api/client.ts`: `uploadPdf(formData): Promise<ApiResponse>`
* Types in `src/types.ts`.
* **Acceptance:** Type-safe fetch; errors surfaced.

**B4. UI components**

* `App.tsx`: file input, optional date input, submit button, loading/error state.
* `components/ResultsGrid.tsx`: render table with **Revenue** and **Gross Profit**; optional caption for `period_end_date`.
* **Acceptance:** Manual test:

  * Choose PDF, set date, submit.
  * See grid with two rows (**no math in UI**).
  * Errors show on bad inputs.

**B5. Polish**

* Minimal **accessible labels**.
* Basic **empty state** and **error copy**.
* **Acceptance:** Clean, readable UI; works end-to-end.

---

### Phase C — Run & (Optional) Tests

**C1. End-to-end sanity**

* Start backend (8000) + frontend (5173).
* Upload a known PDF; verify values.

**C2. (Optional) Pytest**

* Add a couple of unit tests for normalization and parentheses handling.

---

## 8) Risks & Mitigations

* **Label variability:** Target specific labels first; plan to extend in live session.
* **PDF quirks:** If multiple occurrences of labels appear, choose the **first match** (document in `DECISIONS.md`).
* **Locale/formatting:** Only `$`/spaces/parentheses covered; **commas not returned**.

---

## 9) Definition of Done

* **Backend:** `/api/extract/` returns normalized `revenue`, `cos`, `gross_profit` and echoes `period_end_date`.
* **Frontend:** Upload + date → displays **Revenue** & **Gross Profit** in a grid **without UI math**.
* **Dev proxy** works; **no CORS** config needed locally.
* **Docs:** `README.md`, `DECISIONS.md`, `AI_USAGE.md` complete and accurate.
* (Optional) Basic tests pass.

---

## 10) Live Session Prep (deferred work)

* Add **label variants** (e.g., “Total Revenues”, “Consolidated Revenues”).
* Discuss trade-offs: **regex vs table parsing**; robustness vs complexity.
* Extend tests to cover variants and negative cases.

---

### Appendix (Quick Snippets)

**Minimal `requirements.txt`:**

```
Django>=5.0
pdfminer.six>=20231228
pytest>=8.0
```

**Frontend table example (rendered):**

| Metric       | Value  |
| ------------ | ------ |
| Revenue      | 350018 |
| Gross Profit | 203712 |
