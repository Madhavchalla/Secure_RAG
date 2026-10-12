from typing import List
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.document import Document, DocumentPermission


class PermissionResolver:
    """
    Enforces Mandatory Access Control (MAC) and Role-Based Access Control (RBAC).
    Resolves the exact subset of document IDs that the authenticated user is permitted to view.
    """

    @staticmethod
    def get_authorized_document_ids(user: User, db: Session) -> List[int]:
        """
        Calculates authorized document IDs:
        - Admin: All ACTIVE documents.
        - Normal User: ACTIVE documents matching ownership, user-specific permission, or role permission.
        """
        if user.role == "admin":
            docs = db.query(Document.id).filter(
                Document.status == "ACTIVE"
            ).all()
            return [d[0] for d in docs]

        # Standard user permissions
        owned_docs = db.query(Document.id).filter(
            Document.owner_id == user.id,
            Document.status == "ACTIVE"
        ).all()
        owned_ids = {d[0] for d in owned_docs}

        # Role-based or user-specific permission grants
        granted_docs = db.query(DocumentPermission.document_id).join(Document).filter(
            Document.status == "ACTIVE",
            DocumentPermission.can_read == True,
            (DocumentPermission.user_id == user.id) | (DocumentPermission.role == user.role)
        ).all()
        granted_ids = {d[0] for d in granted_docs}

        authorized_ids = list(owned_ids.union(granted_ids))
        return authorized_ids

    @staticmethod
    def can_access_document(user: User, document_id: int, db: Session) -> bool:
        """
        Direct authorization check for a specific document.
        """
        authorized_ids = PermissionResolver.get_authorized_document_ids(user, db)
        return document_id in authorized_ids


# Singleton permission resolver
permission_resolver = PermissionResolver()
