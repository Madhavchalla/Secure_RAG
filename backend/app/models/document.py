from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    mime_type = Column(String(100), nullable=False)
    sensitivity_level = Column(String(20), nullable=False, default="LOW")  # 'LOW', 'MEDIUM', 'HIGH'
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")  # 'ACTIVE', 'QUARANTINED', 'ARCHIVED'
    security_flags = Column(Text, nullable=True, default=None)  # JSON-encoded array of threats
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="documents")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename='{self.filename}' sensitivity='{self.sensitivity_level}' status='{self.status}'>"


class DocumentPermission(Base):
    __tablename__ = "document_permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=True, default=None)  # Role-based access ('admin', 'user')
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, default=None)  # User-specific access
    can_read = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="permissions")
    user = relationship("User", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<DocumentPermission id={self.id} doc_id={self.document_id} role={self.role} user_id={self.user_id}>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    content_preview = Column(String(200), nullable=True)
    chroma_id = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} doc_id={self.document_id} page={self.page_number} chroma_id={self.chroma_id}>"
