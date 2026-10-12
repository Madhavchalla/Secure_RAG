# RAS-RAG Architecture & System Design Document

## 1. System Overview
**RAS-RAG (Risk-Aware Secure Retrieval-Augmented Generation for Privacy-Preserving Document Access)** introduces a defense-in-depth security gateway between user queries, vector search indices, and local Language Model inference engines.

Traditional RAG systems perform vector similarity queries blindly across the entire document corpus. In contrast, RAS-RAG enforces **Mandatory Access Control (MAC)** before semantic search, evaluates composite risk in real time, and dynamically chooses from four policy postures (`ALLOW`, `RESTRICT`, `VERIFY`, `BLOCK`).

---

## 2. Component Architecture

```
+-----------------------------------------------------------------------------------+
|                            Presentation Layer (React 18 + Vite)                  |
|   - Chat Interface with Citations            - Administration & Governance        |
|   - Real-Time Risk Telemetry Display         - Quarantine Inspection Station      |
+-----------------------------------------------------------------------------------+
                                         │  (JWT Authenticated REST APIs)
                                         ▼
+-----------------------------------------------------------------------------------+
|                        API Gateway & Security Layer (FastAPI)                     |
|   - OAuth2 Bearer Token Validation           - Input Sanitization & Rate Bounds   |
|   - Role-Based Access Control (RBAC)         - Structured Audit Logging           |
+-----------------------------------------------------------------------------------+
         │                                       │                       │
         ▼                                       ▼                       ▼
+-----------------------+               +------------------+    +-------------------+
| Pre-Retrieval Auth    |               | Query & Session  |    | Document Pipeline |
| Resolves authorized   |               | Risk Engine      |    | PyMuPDF / docx    |
| document IDs (SQL)    |               | S_q, S_s, S_d, R |    | Heuristic Scanner |
+-----------------------+               +------------------+    +-------------------+
         │                                       │                       │
         ▼                                       ▼                       ▼
+-----------------------------------------------------------------------------------+
|                         Data & Vector Storage Layer                               |
|   - ChromaDB (Embeddings filtered by `$in: authorized_doc_ids`)                   |
|   - SQLite (Transactional storage: Users, Documents, Permissions, Audits)        |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                       Grounded Generation & Privacy Layer                         |
|   - PII Scrubbing (Regex Redaction)          - Guarded XML Prompt Isolation       |
|   - Ollama Local LLM (llama3.2:3b)           - Page & Chunk Citation Generator    |
+-----------------------------------------------------------------------------------+
```

---

## 3. Data Processing Flows

### A. Document Ingestion Pipeline
1. **Upload & Integrity Verification:** File uploaded by Admin; MIME type, size limit (15 MB), and SHA-256 hash calculated.
2. **Text Extraction:** PyMuPDF (`fitz`) or `python-docx` extracts clean text alongside page numbers.
3. **Pre-Ingestion Security Scanner:** Analyzes extracted text against regex signatures for prompt injection (e.g., `ignore previous instructions`, `bypass permissions`).
4. **Quarantine or Active:** Flagged files are marked `QUARANTINED` and excluded from ChromaDB. Clean files are chunked into 500-character segments with 50-character overlap.
5. **Vector Indexing:** Chunks are embedded via Sentence Transformers (`all-MiniLM-L6-v2`) and stored in ChromaDB with metadata: `{doc_id, filename, page, sensitivity, owner_id}`.

### B. Query & Inference Pipeline
1. **Authentication:** User verified via Bearer JWT.
2. **Pre-Retrieval Filter:** System resolves authorized document IDs for user’s role. If empty, request is safely aborted.
3. **Query Threat Analysis ($S_q$):** Query checked for prompt injection, jailbreaks, or exfiltration patterns.
4. **Session Anomaly Evaluation ($S_s$):** Evaluates user's recent security violations over a 15-minute sliding window.
5. **Authorized Vector Retrieval:** ChromaDB searches only among vectors where `doc_id` is authorized.
6. **Document Sensitivity Evaluation ($S_d$):** Highest sensitivity tier mapped to score (`LOW`=10, `MEDIUM`=40, `HIGH`=75).
7. **Risk Calculation & Decision:**
   $$R = \min(100, \, 0.45 S_q + 0.35 S_s + 0.20 S_d)$$
   Includes a threat floor ($R \ge S_q$ when $S_q \ge 80$) to prevent dilution bias.
8. **Policy Execution:**
   - `BLOCK` ($R \ge 80$): Safe refusal, zero context disclosed, incident logged.
   - `VERIFY` ($60 \le R < 80$): Step-up verification required.
   - `RESTRICT` ($30 \le R < 60$): PII masked, context truncated to top 2 chunks.
   - `ALLOW` ($R < 30$): Full context and citations provided.
9. **Inference & Grounding:** Guarded prompt sent to local Ollama instance (`llama3.2:3b`). Citations mapped to exact page numbers.
