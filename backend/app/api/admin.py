import json
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentChunk, DocumentPermission
from app.models.audit import RiskAssessment, AuditLog, SecurityEvent
from app.schemas.auth import UserResponse
from app.schemas.document import DocumentResponse
from app.schemas.admin import AdminDashboardMetrics, QuarantineReviewAction
from app.api.deps import require_admin
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import text_chunker
from app.rag.vector_store import vector_store

router = APIRouter(prefix="/admin", tags=["Administration & Governance"])


@router.get("/metrics", response_model=AdminDashboardMetrics)
def get_dashboard_metrics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieve live operational metrics and risk distribution telemetry.
    """
    total_docs = db.query(Document).count()
    active_docs = db.query(Document).filter(Document.status == "ACTIVE").count()
    quarantined_docs = db.query(Document).filter(Document.status == "QUARANTINED").count()
    total_users = db.query(User).count()
    total_queries = db.query(RiskAssessment).count()

    blocked_queries = db.query(RiskAssessment).filter(RiskAssessment.decision == "BLOCK").count()
    restricted_queries = db.query(RiskAssessment).filter(RiskAssessment.decision == "RESTRICT").count()
    allow_queries = db.query(RiskAssessment).filter(RiskAssessment.decision == "ALLOW").count()
    verify_queries = db.query(RiskAssessment).filter(RiskAssessment.decision == "VERIFY").count()

    security_incidents = db.query(SecurityEvent).count()

    return AdminDashboardMetrics(
        total_documents=total_docs,
        active_documents=active_docs,
        quarantined_documents=quarantined_docs,
        total_users=total_users,
        total_queries=total_queries,
        blocked_queries=blocked_queries,
        restricted_queries=restricted_queries,
        security_incidents=security_incidents,
        risk_distribution={
            "ALLOW": allow_queries,
            "RESTRICT": restricted_queries,
            "VERIFY": verify_queries,
            "BLOCK": blocked_queries,
        }
    )


@router.get("/quarantine", response_model=List[DocumentResponse])
def get_quarantined_documents(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Fetch all documents currently placed in quarantine for administrator review.
    """
    return db.query(Document).filter(Document.status == "QUARANTINED").order_by(Document.created_at.desc()).all()


@router.post("/quarantine/{document_id}/review")
def review_quarantined_document(
    document_id: int,
    review: QuarantineReviewAction,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Administrative review of a quarantined file:
    - If APPROVED: Mark document ACTIVE, chunk text, and index into ChromaDB.
    - If REJECTED: Delete document file and records permanently.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.status == "QUARANTINED"
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Quarantined document not found.")

    client_ip = request.client.host if request.client else "unknown"

    if review.action == "APPROVE":
        doc.status = "ACTIVE"
        if review.sensitivity_level:
            doc.sensitivity_level = review.sensitivity_level

        # Extract, chunk and index into ChromaDB
        pages = DocumentParser.extract_document(doc.file_path, doc.filename)
        chunks = text_chunker.chunk_pages(pages)
        chroma_chunks = []
        for c in chunks:
            c_uuid = f"doc_{doc.id}_chunk_{c['chunk_index']}"
            chunk_row = DocumentChunk(
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                content_preview=c["content_preview"],
                chroma_id=c_uuid,
            )
            db.add(chunk_row)
            chroma_chunks.append({
                "chroma_id": c_uuid,
                "content": c["content"],
                "metadata": {
                    "doc_id": doc.id,
                    "filename": doc.filename,
                    "page": c["page_number"],
                    "chunk_index": c["chunk_index"],
                    "sensitivity": doc.sensitivity_level,
                    "owner_id": doc.owner_id,
                }
            })
        db.commit()
        vector_store.add_chunks(chroma_chunks)

        audit = AuditLog(
            user_id=current_user.id,
            action="QUARANTINE_OVERRIDE_APPROVED",
            resource_type="DOCUMENT",
            resource_id=str(doc.id),
            status="SUCCESS",
            ip_address=client_ip,
            details_json=json.dumps({"filename": doc.filename, "notes": review.notes})
        )
        db.add(audit)
        db.commit()

        return {"message": f"Document '{doc.filename}' approved, marked ACTIVE, and indexed."}

    else:
        # REJECT: purge file and database record
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception:
                pass

        audit = AuditLog(
            user_id=current_user.id,
            action="QUARANTINE_REJECTED_PURGED",
            resource_type="DOCUMENT",
            resource_id=str(doc.id),
            status="SUCCESS",
            ip_address=client_ip,
            details_json=json.dumps({"filename": doc.filename, "notes": review.notes})
        )
        db.add(audit)
        db.delete(doc)
        db.commit()

        return {"message": f"Quarantined document '{doc.filename}' rejected and permanently removed."}


@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List registered system users.
    """
    return db.query(User).order_by(User.id.asc()).all()


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    new_role: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a user's role (admin or user).
    """
    if new_role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.role = new_role
    db.commit()
    return {"message": f"User '{user.username}' role updated to '{new_role}'."}
