# DealMover Intern Case Study: Project Context & Plan

This document outlines the context and step-by-step plan for the DealMover Intern Case Study. The goal is to build a full-stack application that extracts financial data from 10-K PDF documents.

## Project Goal

The primary objective is to create a minimal system that:

1.  Accepts a 10-K PDF file via a web interface.
2.  Extracts "Revenue" and "Cost of Sales" (COS) on the backend.
3.  Normalizes the extracted financial figures.
4.  Calculates "Gross Profit" (`Revenue - COS`) on the backend.
5.  Displays the "Revenue" and "Gross Profit" in a simple grid on the frontend.

## Core Technologies

- **Backend:** Django, `pdfminer.six`
- **Frontend:** Vite, React, TypeScript
- **Development:** Vite dev proxy to handle same-origin requests to the Django backend.

## Key Specifications

### API Response Schema

The backend must return JSON with the following structure:

```json
{
  "period_end_date": "YYYY-MM-DD",
  "results": {
    "revenue": "<string, normalized>",
    "cos": "<string, normalized>",
    "gross_profit": "<string, normalized>"
  }
}
```

### Normalization Rules

- Remove `$` and **all spaces**.
- Convert parentheses to negative: `(123)` → `-123`.
- Return **numeric strings without commas**.

### Error Handling

The API will use the following HTTP status codes for errors:

- **`400`**: Bad Request (e.g., missing file, non-PDF file).
- **`422`**: Unprocessable Entity (e.g., couldn’t extract `revenue` or `cos`).
- **`500`**: Internal Server Error (for any unexpected errors).

### Security

- The file upload endpoint will only accept `application/pdf`.
- Uploaded files will not be persisted on the server beyond the scope of the request processing.

### Development Proxy

- The frontend development server (Vite) will be configured to proxy requests from `/api` to the backend at `http://localhost:8000`. This avoids CORS issues during development.

## Step-by-Step Implementation Plan

This plan is broken down into phases and individual tasks to facilitate step-by-step commits.

---

### Phase A: Backend Development (Django)

**Task A1: Scaffold Django Project**

- [x] Initialize a new Django project in the `/backend` directory.
- [x] Create a Django app named `core`.
- [x] Create a minimal `requirements.txt` with `Django` and `pdfminer.six`.
- [x] Verify the setup by running the development server.

**Task A2: Implement PDF Parsing Utility**

- [x] In the `core` app, create a `parsing.py` file.
- [x] Implement a function `extract_values_from_pdf(file_bytes)` that:
  - Converts the PDF content to text.
  - Finds and extracts the values for "Revenue" and "Cost of Sales".
  - Normalizes the values (removes `$` and spaces, handles `(123)` as negative).
- [x] The function should return a dictionary: `{"revenue": "...", "cos": "..."}`.

**Task A3: Implement Gross Profit Calculation**

- [x] Create a helper function `compute_gross_profit(revenue_str, cos_str)`.
- [x] The function should safely convert the normalized string inputs to numbers, calculate the gross profit, and return it as a string.

**Task A4: Create the API Endpoint**

- [x] In `core/views.py`, create a view for `POST /api/extract/`.
- [x] The view should handle a `multipart/form-data` request containing the PDF file and an optional `period_end_date`.
- [x] Orchestrate the calls to the parsing and calculation functions.
- [x] Return the final JSON response as specified in the PRD.
- [x] Wire up the view in `core/urls.py`.

**Task A5: Implement API Error Handling**

- [x] Add validation and error handling to the API view:
  - **400 Bad Request:** For missing or non-PDF files.
  - **422 Unprocessable Entity:** If "Revenue" or "COS" cannot be extracted.
  - **500 Internal Server Error:** For any other unexpected errors.

---

### Phase B: Frontend Development (Vite + React)

**Task B1: Scaffold Vite Project**

- [x] Initialize a new Vite project with the `react-ts` template in the `/frontend` directory.
- [x] Verify the setup by running the development server (`npm run dev`).

**Task B2: Configure Vite Dev Proxy**

- [x] Modify `frontend/vite.config.ts` to proxy all requests from `/api` to the backend server at `http://localhost:8000`.

**Task B3: Create API Client**

- [x] Create `frontend/src/api/client.ts` to handle the `fetch` request to the backend.
- [x] Define the necessary TypeScript types for the API request and response in `frontend/src/types.ts`.

**Task B4: Build UI Components**

- [x] **`App.tsx`:**
  - Create the main application component.
  - Add state management for the file, date, loading status, and API response/error.
  - Implement the form with a file input, an optional date input, and a submit button.
- [x] **`components/ResultsGrid.tsx`:**
  - Create a component to display the results (`Revenue` and `Gross Profit`) in a table.
  - It should receive the data as props and render it without performing any calculations.

**Task B5: Finalize UI and End-to-End Flow**

- [x] Connect the UI components and the API client.
- [x] Implement the end-to-end flow: select file, submit, show loading state, and display results or an error message.
- [x] Add basic styling for readability.

---

### Phase C: Documentation & Finalization

**Task C1: Write Documentation**

- [x] Update `README.md` with clear setup and run instructions for both the backend and frontend.
- [x] Create a `DECISIONS.md` file to document key architectural choices (e.g., why the proxy is used, why calculations are on the backend).
- [x] Update `AI_USAGE.md` to reflect the prompts and guidance used during development.

**Task C2: End-to-End Testing**

- [ ] Run both frontend and backend servers.
- [ ] Perform a final test by uploading a sample 10-K PDF and verifying that the correct results are displayed.

---

Do you have any questions about this plan? If not, we can begin with the first task: **A1. Scaffold Django Project**. Shall I proceed?
