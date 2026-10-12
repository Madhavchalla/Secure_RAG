import json
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.auth import Token, UserLogin, UserCreate, UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user credentials and return a signed JWT token with role claims.
    Logs successful and failed authentication attempts to the audit log.
    """
    user = db.query(User).filter(User.username == login_data.username).first()
    client_ip = request.client.host if request.client else "unknown"

    if not user or not verify_password(login_data.password, user.hashed_password):
        # Record security audit event for failed login
        audit = AuditLog(
            user_id=user.id if user else None,
            action="USER_LOGIN_FAILED",
            resource_type="AUTH",
            resource_id=login_data.username,
            status="DENIED",
            ip_address=client_ip,
            details_json=json.dumps({"reason": "Invalid credentials", "attempted_user": login_data.username})
        )
        db.add(audit)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is currently disabled."
        )

    # Generate JWT
    token_payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    }
    access_token = create_access_token(
        data=token_payload,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Log successful login
    audit = AuditLog(
        user_id=user.id,
        action="USER_LOGIN_SUCCESS",
        resource_type="AUTH",
        resource_id=str(user.id),
        status="SUCCESS",
        ip_address=client_ip,
        details_json=json.dumps({"username": user.username, "role": user.role})
    )
    db.add(audit)
    db.commit()

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        user_id=user.id
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new standard user account.
    Prevents self-registration with 'admin' role.
    """
    # Enforce safe role assignment: public registration is always 'user'
    assigned_role = "user"

    existing_user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username or email already exists."
        )

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=assigned_role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=new_user.id,
        action="USER_REGISTERED",
        resource_type="USER",
        resource_id=str(new_user.id),
        status="SUCCESS",
        ip_address=client_ip,
        details_json=json.dumps({"username": new_user.username, "email": new_user.email})
    )
    db.add(audit)
    db.commit()

    return new_user


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the authenticated user's profile and active permissions.
    """
    return current_user


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a logout event. Stateless JWTs expire automatically or are cleared client-side.
    """
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_user.id,
        action="USER_LOGOUT",
        resource_type="AUTH",
        resource_id=str(current_user.id),
        status="SUCCESS",
        ip_address=client_ip,
        details_json=json.dumps({"username": current_user.username})
    )
    db.add(audit)
    db.commit()
    return {"message": "Successfully logged out."}
