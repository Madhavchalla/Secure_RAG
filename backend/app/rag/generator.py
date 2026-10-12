import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.audit import RiskAssessment, AuditLog, SecurityEvent
from app.schemas.rag import QueryResponse, Citation, RiskBreakdown
from app.security.permissions import permission_resolver
from app.security.pii_masker import pii_masker
from app.risk_engine.query_analyzer import query_analyzer
from app.risk_engine.session_evaluator import session_evaluator
from app.risk_engine.scorer import risk_scorer
from app.risk_engine.decision_matrix import decision_matrix
from app.rag.vector_store import vector_store
from app.rag.prompt_builder import GuardedPromptBuilder
from app.rag.ollama_client import ollama_client


class SecureRAGOrchestrator:
    """
    End-to-end secure RAG pipeline enforcing pre-retrieval authorization,
    multi-factor risk evaluation, context sanitization, grounded generation,
    and auditable decision logging.
    """

    def process_query(
        self,
        query: str,
        user: User,
        db: Session,
        client_ip: str = "127.0.0.1"
    ) -> QueryResponse:
        # ------------------------------------------------------------------
        # STAGE A: Authentication & Mandatory Access Control Boundary
        # ------------------------------------------------------------------
        authorized_doc_ids = permission_resolver.get_authorized_document_ids(user, db)

        if not authorized_doc_ids:
            # User is authorized to zero documents in the system
            reasons = ["No accessible or authorized documents found for current user account."]
            risk_breakdown = RiskBreakdown(
                query_risk_score=0.0,
                session_risk_score=0.0,
                doc_sensitivity_score=0.0,
                final_risk_score=0.0,
                decision="BLOCK",
                reasons=reasons,
            )

            # Audit record
            audit = AuditLog(
                user_id=user.id,
                action="RAG_QUERY_DENIED_NO_PERMISSIONS",
                resource_type="QUERY",
                resource_id=query[:100],
                status="DENIED",
                ip_address=client_ip,
                details_json=json.dumps({"query": query, "reasons": reasons})
            )
            db.add(audit)
            db.commit()

            return QueryResponse(
                query=query,
                decision="BLOCK",
                answer="Access denied: You do not have permission to access any active organizational documents.",
                citations=[],
                risk_assessment=risk_breakdown,
                is_restricted=False,
                disclaimer="Strict authorization policy enforced. No documents were retrieved."
            )

        # ------------------------------------------------------------------
        # STAGE B: Query Threat Analysis
        # ------------------------------------------------------------------
        q_score, q_reasons = query_analyzer.analyze(query)

        # ------------------------------------------------------------------
        # STAGE C: Session Anomaly Risk Evaluation
        # ------------------------------------------------------------------
        s_score, s_reasons = session_evaluator.evaluate(user.id, db)

        # ------------------------------------------------------------------
        # STAGE D: Mandatory Pre-Retrieval Filtered Vector Search
        # ------------------------------------------------------------------
        raw_candidates = vector_store.search_authorized(
            query=query,
            authorized_doc_ids=authorized_doc_ids,
            top_k=4
        )

        # ------------------------------------------------------------------
        # STAGE E: Candidate Document Sensitivity Evaluation
        # ------------------------------------------------------------------
        highest_sensitivity = "LOW"
        sensitivity_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

        for c in raw_candidates:
            c_sens = c.get("metadata", {}).get("sensitivity", "LOW").upper()
            if sensitivity_rank.get(c_sens, 1) > sensitivity_rank.get(highest_sensitivity, 1):
                highest_sensitivity = c_sens

        doc_score = risk_scorer.map_doc_sensitivity(highest_sensitivity)

        # ------------------------------------------------------------------
        # STAGE F: Composite Risk Calculation & Decision Matrix
        # ------------------------------------------------------------------
        final_risk = risk_scorer.calculate(q_score, s_score, doc_score)
        combined_reasons = q_reasons + s_reasons
        if not combined_reasons:
            combined_reasons.append("Baseline operational risk within acceptable organizational thresholds.")

        policy = decision_matrix.evaluate_decision(final_risk)
        decision = policy["decision"]

        risk_breakdown = RiskBreakdown(
            query_risk_score=q_score,
            session_risk_score=s_score,
            doc_sensitivity_score=doc_score,
            final_risk_score=final_risk,
            decision=decision,
            reasons=combined_reasons,
        )

        # Record Risk Assessment Telemetry
        assessment_row = RiskAssessment(
            user_id=user.id,
            query_text=query,
            query_risk_score=q_score,
            session_risk_score=s_score,
            doc_sensitivity_score=doc_score,
            final_risk_score=final_risk,
            decision=decision,
            reasons=json.dumps(combined_reasons),
        )
        db.add(assessment_row)

        # ------------------------------------------------------------------
        # STAGE G: Posture Execution (ALLOW / RESTRICT / VERIFY / BLOCK)
        # ------------------------------------------------------------------
        if decision == "BLOCK":
            # Hard refusal: Zero context disclosure
            audit = AuditLog(
                user_id=user.id,
                action="RAG_QUERY_BLOCKED",
                resource_type="QUERY",
                resource_id=query[:100],
                status="DENIED",
                ip_address=client_ip,
                details_json=json.dumps({"risk_score": final_risk, "reasons": combined_reasons})
            )
            security_evt = SecurityEvent(
                user_id=user.id,
                event_type="PROMPT_INJECTION_OR_HIGH_RISK_QUERY",
                severity="HIGH" if final_risk < 90 else "CRITICAL",
                description=f"Query blocked due to critical risk score {final_risk}. Query snippet: '{query[:80]}'",
                metadata_json=json.dumps({"reasons": combined_reasons, "query": query})
            )
            db.add(audit)
            db.add(security_evt)
            db.commit()

            return QueryResponse(
                query=query,
                decision="BLOCK",
                answer="Request blocked: This query triggered high-risk security thresholds. An incident record has been logged.",
                citations=[],
                risk_assessment=risk_breakdown,
                is_restricted=False,
                disclaimer="Adaptive security defense engaged. Context access aborted."
            )

        if decision == "VERIFY":
            # Step-up verification requirement notice
            audit = AuditLog(
                user_id=user.id,
                action="RAG_QUERY_VERIFICATION_REQUIRED",
                resource_type="QUERY",
                resource_id=query[:100],
                status="WARNING",
                ip_address=client_ip,
                details_json=json.dumps({"risk_score": final_risk, "reasons": combined_reasons})
            )
            db.add(audit)
            db.commit()

            return QueryResponse(
                query=query,
                decision="VERIFY",
                answer="Verification required: The requested content involves elevated document sensitivity. Administrative approval is required before this information can be released.",
                citations=[],
                risk_assessment=risk_breakdown,
                is_restricted=True,
                disclaimer="Step-up verification required."
            )

        # Process context under ALLOW or RESTRICT
        is_restricted = (decision == "RESTRICT")
        active_candidates = raw_candidates

        if is_restricted:
            # Under RESTRICT: Limit chunk count and mask PII
            active_candidates = raw_candidates[:2]
            sanitized_chunks = []
            for c in active_candidates:
                masked_content, _ = pii_masker.mask(c["content"], mask_financial=True)
                sanitized_chunks.append({
                    "chroma_id": c["chroma_id"],
                    "content": masked_content,
                    "metadata": c["metadata"],
                })
            active_candidates = sanitized_chunks

        # Check for zero candidate matches
        if not active_candidates:
            audit = AuditLog(
                user_id=user.id,
                action="RAG_QUERY_NO_GROUNDING_FOUND",
                resource_type="QUERY",
                resource_id=query[:100],
                status="SUCCESS",
                ip_address=client_ip,
                details_json=json.dumps({"query": query})
            )
            db.add(audit)
            db.commit()

            return QueryResponse(
                query=query,
                decision=decision,
                answer="The available authorized documents do not contain sufficient information to answer this question.",
                citations=[],
                risk_assessment=risk_breakdown,
                is_restricted=is_restricted,
                disclaimer="Factual grounding check: No relevant authorized excerpts passed similarity threshold."
            )

        # ------------------------------------------------------------------
        # STAGE H: Prompt Construction & LLM Inference
        # ------------------------------------------------------------------
        guarded_prompt = GuardedPromptBuilder.build_prompt(
            query=query,
            chunks=active_candidates,
            is_restricted=is_restricted
        )

        llm_output = ollama_client.generate(guarded_prompt, active_candidates)
        final_answer = llm_output["answer"]

        # Post-generation PII scrubbing if restricted
        if is_restricted:
            final_answer, _ = pii_masker.mask(final_answer, mask_financial=True)

        # ------------------------------------------------------------------
        # STAGE I: Format Citations & Audit Success
        # ------------------------------------------------------------------
        citations = []
        for c in active_candidates:
            meta = c.get("metadata", {})
            citations.append(Citation(
                document_id=int(meta.get("doc_id", 0)),
                filename=str(meta.get("filename", "Unknown")),
                page_number=int(meta.get("page", 1)),
                chunk_index=int(meta.get("chunk_index", 0)),
                snippet=c["content"][:180].replace("\n", " "),
                sensitivity_level=str(meta.get("sensitivity", "LOW")),
            ))

        audit = AuditLog(
            user_id=user.id,
            action="RAG_QUERY_SUCCESS",
            resource_type="QUERY",
            resource_id=query[:100],
            status="SUCCESS",
            ip_address=client_ip,
            details_json=json.dumps({
                "decision": decision,
                "risk_score": final_risk,
                "citations_count": len(citations),
                "is_restricted": is_restricted,
            })
        )
        db.add(audit)
        db.commit()

        return QueryResponse(
            query=query,
            decision=decision,
            answer=final_answer,
            citations=citations,
            risk_assessment=risk_breakdown,
            is_restricted=is_restricted,
            disclaimer="Response grounded in authorized document content with active risk monitoring." if not is_restricted else "PII masking and policy restriction applied."
        )


# Singleton RAG orchestrator instance
rag_orchestrator = SecureRAGOrchestrator()
