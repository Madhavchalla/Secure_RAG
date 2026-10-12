from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.rag import QueryRequest, QueryResponse
from app.api.deps import get_current_user
from app.rag.generator import rag_orchestrator

router = APIRouter(prefix="/rag", tags=["Secure RAG Engine"])


@router.post("/query", response_model=QueryResponse)
def query_rag_assistant(
    request: Request,
    query_in: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a secure RAG inquiry through the RAS-RAG pipeline:
    - Pre-retrieval Mandatory Access Control (MAC) boundary enforcement.
    - Query threat scoring and prompt-injection detection.
    - Session anomaly risk evaluation.
    - Candidate document sensitivity assessment.
    - Decision posture evaluation (ALLOW, RESTRICT, VERIFY, BLOCK).
    - Grounded generation with citation attribution and audit logging.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    response = rag_orchestrator.process_query(
        query=query_in.query,
        user=current_user,
        db=db,
        client_ip=client_ip
    )
    return response
