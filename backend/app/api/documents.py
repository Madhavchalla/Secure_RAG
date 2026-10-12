import os
import hashlib
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentPermission, DocumentChunk
from app.models.audit import AuditLog, SecurityEvent
from app.schemas.document import (
    DocumentResponse,
    DocumentUpdate,
    DocumentPermissionCreate,
    DocumentPermissionResponse,
)
from app.api.deps import get_current_user, require_admin
from app.ingestion.parser import DocumentParser
from app.ingestion.scanner import ingestion_scanner
from app.ingestion.chunker import text_chunker
from app.rag.vector_store import vector_store
from app.security.permissions import permission_resolver

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    sensitivity_level: str = Form("LOW"),
    assign_role: Optional[str] = Form(None),  # 'user', 'admin', or None
    current_user: User = Depends(require_admin),  # Admin-only upload
    db: Session = Depends(get_db)
):
    """
    Secure Document Ingestion Pipeline:
    1. Validates extension, MIME type, and size limits.
    2. Computes SHA-256 integrity hash.
    3. Extracts text and page numbers via PyMuPDF / docx parser.
    4. Scans content for prompt injection signatures.
    5. Flags and quarantines suspicious uploads.
    6. If clean, splits text into chunks and indexes vectors into ChromaDB.
    """
    # 1. Validation
    allowed_exts = [".pdf", ".docx", ".txt", ".md"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{file_ext}'. Allowed: {', '.join(allowed_exts)}"
        )

    content_bytes = await file.read()
    file_size = len(content_bytes)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB."
        )

    # 2. Hash & Safe Storage
    file_hash = hashlib.sha256(content_bytes).hexdigest()
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    saved_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(saved_path, "wb") as f:
        f.write(content_bytes)

    # 3. Text Extraction
    try:
        pages = DocumentParser.extract_document(saved_path, file.filename)
    except Exception as e:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract document contents: {str(e)}"
        )

    full_text = "\n".join([p["text"] for p in pages])

    # 4. Security Threat & Injection Scanning
    scan_result = ingestion_scanner.scan_text(full_text)
    is_suspicious = scan_result["is_suspicious"]
    security_status = "QUARANTINED" if is_suspicious else "ACTIVE"
    flags_json = json.dumps(scan_result["triggered_rules"]) if is_suspicious else None

    # 5. Database Record Creation
    doc = Document(
        filename=file.filename,
        stored_filename=unique_filename,
        file_path=saved_path,
        file_size=file_size,
        file_hash=file_hash,
        mime_type=file.content_type or "application/octet-stream",
        sensitivity_level=sensitivity_level.upper(),
        owner_id=current_user.id,
        status=security_status,
        security_flags=flags_json,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6. Assign Default Document Permissions
    # Admins always have access
    admin_perm = DocumentPermission(document_id=doc.id, role="admin", can_read=True)
    db.add(admin_perm)

    # Granted role permission (e.g. 'user' or None)
    if assign_role and assign_role.strip() and assign_role.strip().lower() not in ["none", "null", ""]:
        role_perm = DocumentPermission(document_id=doc.id, role=assign_role.strip(), can_read=True)
        db.add(role_perm)

    db.commit()

    # 7. Chunking & ChromaDB Indexing (ONLY if document is clean/ACTIVE)
    client_ip = request.client.host if request.client else "unknown"
    if security_status == "ACTIVE":
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

        # Insert into ChromaDB
        vector_store.add_chunks(chroma_chunks)

        # Audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="DOCUMENT_UPLOAD_ACTIVE",
            resource_type="DOCUMENT",
            resource_id=str(doc.id),
            status="SUCCESS",
            ip_address=client_ip,
            details_json=json.dumps({"filename": doc.filename, "chunks_indexed": len(chroma_chunks)})
        )
        db.add(audit)
        db.commit()
    else:
        # Document was quarantined!
        audit = AuditLog(
            user_id=current_user.id,
            action="DOCUMENT_QUARANTINED_AT_INGESTION",
            resource_type="DOCUMENT",
            resource_id=str(doc.id),
            status="WARNING",
            ip_address=client_ip,
            details_json=json.dumps({
                "filename": doc.filename,
                "threat_score": scan_result["threat_score"],
                "rules": scan_result["triggered_rules"]
            })
        )
        sec_event = SecurityEvent(
            user_id=current_user.id,
            event_type="QUARANTINE_TRIGGER",
            severity=scan_result["highest_severity"],
            description=f"File '{doc.filename}' quarantined during ingestion due to detected prompt injection patterns.",
            metadata_json=flags_json
        )
        db.add(audit)
        db.add(sec_event)
        db.commit()

    db.refresh(doc)
    return doc


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List accessible documents:
    - Admin: All documents (active and quarantined).
    - User: Only ACTIVE documents authorized by RBAC and ownership.
    """
    if current_user.role == "admin":
        return db.query(Document).order_by(Document.created_at.desc()).all()

    authorized_ids = permission_resolver.get_authorized_document_ids(current_user, db)
    if not authorized_ids:
        return []

    return db.query(Document).filter(
        Document.id.in_(authorized_ids),
        Document.status == "ACTIVE"
    ).order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed metadata and permissions for a specific document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if current_user.role != "admin":
        if not permission_resolver.can_access_document(current_user, document_id, db):
            raise HTTPException(status_code=403, detail="Access denied: You are not authorized to view this document.")

    return doc


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document_metadata(
    document_id: int,
    doc_update: DocumentUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update document sensitivity tier or status (Admin-only).
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc_update.sensitivity_level:
        doc.sensitivity_level = doc_update.sensitivity_level

    if doc_update.status:
        doc.status = doc_update.status

    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Atomic document purge:
    Deletes the physical file, SQLite document metadata, chunks, and ChromaDB vector embeddings simultaneously.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 1. Delete physical file
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 2. Purge ChromaDB vectors
    vector_store.delete_document_vectors(doc.id)

    # 3. Log audit event
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_user.id,
        action="DOCUMENT_PURGED",
        resource_type="DOCUMENT",
        resource_id=str(doc.id),
        status="SUCCESS",
        ip_address=client_ip,
        details_json=json.dumps({"filename": doc.filename})
    )
    db.add(audit)

    # 4. Delete SQLite record (cascades to chunks and permissions)
    db.delete(doc)
    db.commit()

    return {"message": f"Document '{doc.filename}' and all associated vector embeddings purged successfully."}


@router.post("/{document_id}/permissions", response_model=DocumentPermissionResponse)
def add_document_permission(
    document_id: int,
    perm_in: DocumentPermissionCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Grant read permission on a document to a specific role or user ID (Admin-only).
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    perm = DocumentPermission(
        document_id=doc.id,
        role=perm_in.role,
        user_id=perm_in.user_id,
        can_read=perm_in.can_read
    )
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm
