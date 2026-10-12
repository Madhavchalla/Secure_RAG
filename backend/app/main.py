import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.document import Document, DocumentPermission, DocumentChunk
from app.models.audit import RiskAssessment, AuditLog, SecurityEvent
from app.api import auth, documents, rag, admin, audit


def init_database_seeds():
    """
    Initialize SQLite database tables and seed baseline administrative
    and standard user accounts if they do not already exist.
    """
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check or create default Admin account
        admin_user = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()
        if not admin_user:
            admin_user = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
                is_active=True,
            )
            db.add(admin_user)

        # Check or create default standard user
        analyst_user = db.query(User).filter(User.username == settings.DEFAULT_USER_USERNAME).first()
        if not analyst_user:
            analyst_user = User(
                username=settings.DEFAULT_USER_USERNAME,
                email=settings.DEFAULT_USER_EMAIL,
                hashed_password=hash_password(settings.DEFAULT_USER_PASSWORD),
                role="user",
                is_active=True,
            )
            db.add(analyst_user)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database seeding failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and seed data
    init_database_seeds()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=f"{settings.APP_NAME} - Risk-Aware Secure RAG API",
    version="1.0.0",
    description="Risk-Aware Secure Retrieval-Augmented Generation for Privacy-Preserving Document Access",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(audit.router, prefix="/api")


@app.get("/api/health", tags=["Health"])
def health_check():
    """
    Service health check endpoint verifying backend availability and runtime configuration.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
        "storage": {
            "database": "sqlite",
            "uploads": os.path.exists(settings.UPLOAD_DIR),
            "chroma_dir": os.path.exists(settings.CHROMA_PERSIST_DIR),
        },
        "risk_engine": {
            "weights": {
                "query": settings.RISK_WEIGHT_QUERY,
                "session": settings.RISK_WEIGHT_SESSION,
                "doc_sensitivity": settings.RISK_WEIGHT_DOC_SENSITIVITY,
            },
            "thresholds": {
                "allow": settings.THRESHOLD_ALLOW,
                "restrict": settings.THRESHOLD_RESTRICT,
                "verify": settings.THRESHOLD_VERIFY,
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
