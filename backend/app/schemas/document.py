from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentPermissionCreate(BaseModel):
    role: Optional[str] = None  # 'admin', 'user', or custom role
    user_id: Optional[int] = None
    can_read: bool = True


class DocumentPermissionResponse(BaseModel):
    id: int
    document_id: int
    role: Optional[str] = None
    user_id: Optional[int] = None
    can_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUpdate(BaseModel):
    sensitivity_level: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH)$")
    status: Optional[str] = Field(None, pattern="^(ACTIVE|QUARANTINED|ARCHIVED)$")


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    mime_type: str
    sensitivity_level: str
    owner_id: int
    status: str
    security_flags: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    permissions: List[DocumentPermissionResponse] = []

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    page_number: int
    content_preview: Optional[str] = None
    chroma_id: str

    class Config:
        from_attributes = True
