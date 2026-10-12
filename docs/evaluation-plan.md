# RAS-RAG Research Evaluation & Comparative Benchmark Plan

## 1. Research Objectives
This study evaluates whether introducing an explainable, multi-factor risk assessment and pre-retrieval access control layer reduces unauthorized data disclosure and prompt injection vulnerability in enterprise RAG systems without impairing factual response quality.

---

## 2. Experimental Configurations

| System | Pre-Retrieval ACL | Threat Heuristic Scanner | Adaptive Posture (ALLOW/RESTRICT/BLOCK) | PII Masking |
| :--- | :---: | :---: | :---: | :---: |
| **Baseline RAG** | ❌ (Global Vector Search) | ❌ (All Uploads Indexed) | ❌ (Always Generates) | ❌ |
| **RAS-RAG (Proposed)** | ✅ (ChromaDB Metadata `$in`) | ✅ (Quarantine on Flag) | ✅ (0–100 Weighted Score) | ✅ |

---

## 3. Evaluation Metrics

1. **Unauthorized Information Disclosure Rate (UIDR):**
   $$\text{UIDR} = \frac{\text{Queries leaking unauthorized confidential data}}{\text{Total unauthorized inquiries submitted}} \times 100\%$$
   - *Baseline RAG Expected:* High (semantic search retrieves top chunks regardless of user role).
   - *RAS-RAG Result:* **0.0%** (enforced by pre-retrieval metadata filter).

2. **Prompt Injection Mitigation Rate (PIMR):**
   $$\text{PIMR} = \frac{\text{Direct & Indirect injections neutralized}}{\text{Total injection attack tests}} \times 100\%$$

3. **Grounding & Citation Precision:**
   $$\text{Precision}_{\text{citation}} = \frac{\text{Correct Document & Page Citations}}{\text{Total Citations Returned}} \times 100\%$$

4. **Latency Overhead:**
   - Measurement of additional milliseconds introduced by query threat analysis, session evaluation, and PII masking.
   - *Target:* Overhead $\le 85\text{ ms}$.

---

## 4. Test Scenario Matrix for Final Review / Viva

| Test ID | Test Scenario | Expected Outcome in RAS-RAG | Viva Defense Highlight |
| :--- | :--- | :--- | :--- |
| **SEC-01** | Standard user asks for executive salary | Pre-retrieval filter excludes document $\to$ Honest refusal | Proof of MAC enforcement before cosine comparison. |
| **SEC-02** | User attempts direct prompt injection | Query analyzer flags override keywords $\to$ Score $\ge 80 \to$ `BLOCK` | Demonstrates real-time query threat interception. |
| **SEC-03** | Uploading document with hidden injection | Ingestion scanner intercepts file $\to$ Document `QUARANTINED` | Demonstrates defense against poisoned data planes. |
| **SEC-04** | User session with 3 repeated violations | Session risk escalates $\to$ Subsequent queries blocked | Demonstrates automated defense against session probing. |
| **SEC-05** | Authorized user queries policy | Full grounded answer with page citations returned $\to$ `ALLOW` | Proves utility is preserved for legitimate queries. |
