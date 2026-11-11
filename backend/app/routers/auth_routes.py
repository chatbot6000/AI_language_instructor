"""Register / login / me."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    get_user_by_username,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models import AiConfig, User
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    username = body.username.strip()
    if get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(username=username, password_hash=hash_password(body.password))
    db.add(user)
    db.flush()  # get user.id before creating related AiConfig

    # Default AI config points at local Ollama OpenAI-compatible API
    db.add(
        AiConfig(
            user_id=user.id,
            base_url="http://127.0.0.1:11434/v1",
            model="llama3.2",
            api_key="",
            temperature="0.7",
        )
    )
    db.commit()

    return TokenResponse(access_token=create_access_token(user.username))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_user_by_username(db, body.username.strip())
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
