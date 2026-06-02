from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session

from app.auth.jwt import JWTService
from app.auth.password import PasswordService
from app.auth.schemas import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
    UpdateUserRequest,
)
from app.auth.utils import bearer_schema, get_user
from app.db.engine import sync_session
from app.repositories.exceptions import NotFoundException
from app.repositories.user import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def get_session():
    with sync_session() as session:
        yield session


@router.post("/signup", response_model=TokenResponse, status_code=HTTPStatus.CREATED)
def signup(body: SignupRequest, session: Session = Depends(get_session)):
    repo = UserRepository(session)

    try:
        repo.get_by_username(body.username)
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Username already taken"
        )
    except NotFoundException:
        pass

    password_hash = PasswordService.hash_password(body.password)
    user = repo.create(username=body.username, password_hash=password_hash)

    access_token = JWTService.create_access_token(
        user_id=str(user.id), token_version=user.token_version
    )
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    repo = UserRepository(session)

    try:
        user = repo.get_by_username(body.username)
    except NotFoundException:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid credentials"
        )

    if not PasswordService.verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid credentials"
        )

    repo.update_last_login(user)

    access_token = JWTService.create_access_token(
        user_id=str(user.id), token_version=user.token_version
    )
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=HTTPStatus.NO_CONTENT)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    UserRepository(session).increment_token_version(current_user)


@router.get("/me", response_model=UserResponse)
def me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    return UserResponse(id=str(current_user.id), username=current_user.username)


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UpdateUserRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    repo = UserRepository(session)

    if body.username is not None:
        try:
            repo.get_by_username(body.username)
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="Username already taken"
            )
        except NotFoundException:
            pass
        repo.update(current_user, username=body.username)

    if body.password is not None:
        password_hash = PasswordService.hash_password(body.password)
        repo.update_password(current_user, password_hash=password_hash)

    return UserResponse(id=str(current_user.id), username=current_user.username)
