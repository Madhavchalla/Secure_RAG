# RAS-RAG API Reference Guide

FastAPI automatically serves interactive Swagger UI documentation at:
**`http://localhost:8000/docs`**

---

## 1. Authentication Endpoints

### `POST /api/auth/login`
- **Description:** Authenticates user and returns JWT bearer token with role claims.
- **Request Body:**
  ```json
  {
    "username": "admin",
    "password": "AdminSecure@2026"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "role": "admin",
    "username": "admin",
    "user_id": 1
  }
  ```

### `GET /api/auth/me`
- **Headers:** `Authorization: Bearer <token>`
- **Response:** Profile details of the current authenticated user.

---

## 2. Document Endpoints

### `POST /api/documents/upload` (Admin Only)
- **Headers:** `Authorization: Bearer <admin_token>`
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `file`: Binary document (.pdf, .docx, .txt, .md)
  - `sensitivity_level`: `"LOW"`, `"MEDIUM"`, or `"HIGH"`
  - `assign_role`: `"user"`, `"admin"`, or `""`

### `GET /api/documents/`
- **Headers:** `Authorization: Bearer <token>`
- **Response:** Array of accessible documents based on user role and permissions.

### `DELETE /api/documents/{id}` (Admin Only)
- **Description:** Atomically purges physical file, SQLite records, chunks, and ChromaDB vector embeddings.

---

## 3. Secure RAG Endpoints

### `POST /api/rag/query`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "query": "How many days of annual leave do employees receive?"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "query": "How many days of annual leave do employees receive?",
    "decision": "ALLOW",
    "answer": "According to Annual Leave and Attendance Policy (Page 1), employees receive 24 days of paid leave...",
    "citations": [
      {
        "document_id": 1,
        "filename": "01_leave_and_attendance_policy.txt",
        "page_number": 1,
        "chunk_index": 0,
        "snippet": "Every full-time employee is credited with 24 days...",
        "sensitivity_level": "LOW"
      }
    ],
    "risk_assessment": {
      "query_risk_score": 0.0,
      "session_risk_score": 0.0,
      "doc_sensitivity_score": 10.0,
      "final_risk_score": 2.0,
      "decision": "ALLOW",
      "reasons": ["Baseline operational risk within acceptable organizational thresholds."]
    },
    "is_restricted": false
  }
  ```

---

## 4. Governance & Audit Endpoints

### `GET /api/admin/metrics` (Admin Only)
- **Response:** Summary metrics: total documents, active, quarantined, total queries, blocked count, and risk distribution breakdown.

### `GET /api/admin/quarantine` (Admin Only)
- **Response:** List of files flagged for prompt injection awaiting review.

### `POST /api/admin/quarantine/{id}/review` (Admin Only)
- **Request Body:**
  ```json
  {
    "action": "APPROVE",
    "sensitivity_level": "LOW",
    "notes": "Verified false positive by admin."
  }
  ```

### `GET /api/audit/logs` (Admin Only)
- **Query Params:** `?status_filter=SUCCESS&limit=50&offset=0`
