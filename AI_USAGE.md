# AI Usage & Collaboration Guidelines

This document explains **how AI was used** to build the DealMover Financial Data Extractor, what decisions remained **human-owned**, and how to **safely and productively** keep using AI as a context engineer.

---

## 1) Philosophy

* **AI as accelerator, not autopilot.**
  I used AI to draft boilerplate, propose options, and surface edge cases. I (human) made all final design choices, reconciled trade-offs, and fixed the code where the AI’s draft didn’t meet the spec.
* **Backend is the source of truth.**
  AI suggestions never changed the fundamental decisions: all normalization and math (gross profit) happen on the **backend**.
* **Spec-first, code-second.**
  Every AI-assisted change was checked against our **PRD.md** and **DECISIONS.md**. If a suggestion conflicted with the spec, I rejected or adapted it.

---

## 2) Where AI Helped (and how I verified)

### 2.1 Boilerplate & Scaffolding

* **Django + app structure** (health route, URLs, view skeletons)
* **Vite + React + TS** (basic component structure, typed client)
* **Proxy config** for `/api` in `vite.config.ts`

**Human verification:** Ran servers, hit `/api/health`, smoke-tested endpoints with `curl`, and checked frontend via manual E2E.

### 2.2 Parser Iteration & Debugging

* Built the initial **pdfminer.six** flow.
* Iteratively refined regex and heuristics to handle:

  * **Label variants**: `Cost of Sales/Revenue/Revenues`
  * **Split thousands**: commas **or spaces** (e.g., `146 306`)
  * **Year tokens** filtering: skip bare `1900–2100`
  * **Look-ahead** logic: prefer **`$` tokens**; else **leftmost** ≥4-digit token
  * **Normalization**: remove `$`, spaces, commas, periods; `(123)` → `-123`

**Human verification:**
I validated against a real 10-K (`Form 10-K.pdf`) until results matched expected values:

* `revenue = 307394`
* `cos = 133332`
* `gross_profit = 174062`

### 2.3 Error Semantics & API Shape

* Drafted consistent HTTP codes (`400/422/500`) and response schema.
* Frontend **does not compute** values—purely displays backend data.

**Human verification:**
`curl` tests for happy path + negatives; manual UI check.

---

## 3) What AI Did **Not** Decide

* **Architecture choices**: backend computation, API contract, dev proxy, label scope (variants deferred).
* **Heuristic boundaries**: Rule A (leftmost/first-after-label), look-ahead windows, money-like filtering.
* **Acceptance thresholds**: any change had to pass concrete `curl`/UI tests with the provided 10-K.

---

## 4) Prompting Strategy (for future contributors)

* **Context pack first**: include the relevant file excerpts or current code **inline** in the prompt.
* **Pin constraints**: restate non-negotiables (backend math; normalization rules; leftmost value).
* **Ask for diffs**: request “drop-in replacement” snippets or minimal patch blocks to reduce churn.
* **One step at a time**: e.g., “Only update `_best_number_after_label`, nothing else.”

**Example prompt (parser tweak):**

> We must keep Rule A (leftmost / first-after-label) and normalization rules. Current issue: revenue mis-parses as “202” on the label line with no `$`. Provide a minimal change to `_best_number_after_label` so it only accepts money-like tokens or returns None to force look-ahead. Show the exact function only.

---

## 5) Review & Safety Checklist

Before merging any AI-suggested change:

* **Spec alignment**

  * [ ] Still computes on backend only
  * [ ] Response schema unchanged
  * [ ] Normalization unchanged
* **Parser sanity**

  * [ ] Doesn’t match bare years
  * [ ] Accepts space/comma thousands
  * [ ] Same-line requires money-like tokens or defers to look-ahead
  * [ ] Look-ahead prefers `$`, then leftmost ≥4 digits
* **Runtime checks**

  * [ ] `python manage.py runserver` clean
  * [ ] `curl` happy path returns sensible magnitudes
  * [ ] `curl` edge cases return 400/422/500 as expected
  * [ ] Frontend renders Revenue & Gross Profit without UI math
* **Diff hygiene**

  * [ ] Only intended functions/files changed
  * [ ] No secrets, no logging sensitive data

---

## 6) Commit Hygiene & Traceability

* **Tag AI-assisted commits** with succinct intent:

  * `feat(parser):` new capability
  * `fix(parser):` correct extraction/normalization
  * `chore(docs):` PRD/README/DECISIONS updates
* **Summarize the reason** (e.g., “avoid year tokens”, “require \$ on look-ahead”).
* If the patch fixes a specific artifact, **quote the mis-parse** in the commit message for future grep.

**Examples:**

```
fix(parser): avoid tiny same-line fragments; force look-ahead when no money-like token
fix(parser): require $ on look-ahead lines; pick leftmost amount (first column)
```

---

## 7) Known Limits (by design)

* **No OCR**: PDFs must be text-based.
* **Narrow labels** (for v1): “Revenues” and “Cost of (Sales|Revenue|Revenues)”.
* **Column choice**: leftmost value during look-ahead (matches tested `period_end_date=2023-12-31`).
* **UI**: purely presentational; no formatting/commas added on the client.

---

## 8) Extending with AI (recommended patterns)

* **Label variants**: provide 3–5 real lines from target PDFs; ask AI for **regex set + tests**, not just regex.
* **Period-aware selection**: give AI an example table block; instruct it to map `period_end_date` to the correct **column index** and still fall back safely.
* **Number formatting in UI**: ask for a **pure-presentational formatter** that takes strings and returns a formatted string (no math).

---

## 9) Privacy & Data Handling

* Do **not** paste confidential PDFs into prompts.
* If you must share an excerpt for debugging, **redact amounts and names** while keeping structure.
* Never include keys/secrets in prompts or code samples.

---

## 10) TL;DR

* I used AI to **draft boilerplate** and **debug the parser**, but I **owned the architecture, constraints, and final code**.
* Every AI suggestion was verified against real input and our spec.
* Keep using AI as a **context engineer**: provide rich, relevant context; request minimal, testable patches; and validate with `curl` + UI.


