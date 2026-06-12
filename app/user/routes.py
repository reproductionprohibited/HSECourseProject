import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session

from app.user.jwt import JWTService
from app.user.password import PasswordService
from app.user.schemas import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
    UpdateUserRequest,
)
from app.user.utils import bearer_schema, get_user
from app.db.engine import sync_session
from app.repositories.exceptions import NotFoundException
from app.repositories.user import UserRepository
from app.repositories.route import RouteRepository
from app.repositories.impression import ImpressionRepository
from app.routes.schemas import RouteListItemResponse
from app.impressions.schemas import ImpressionResponse

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/user", tags=["users"])


def get_session():
    with sync_session() as session:
        yield session


@auth_router.post(
    "/signup", response_model=TokenResponse, status_code=HTTPStatus.CREATED
)
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


@auth_router.post("/login", response_model=TokenResponse)
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


@auth_router.post("/logout", status_code=HTTPStatus.NO_CONTENT)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    UserRepository(session).increment_token_version(current_user)


@auth_router.get("/me", response_model=UserResponse)
def me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    return UserResponse(id=str(current_user.id), username=current_user.username)


@auth_router.patch("/me", response_model=UserResponse)
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


@users_router.get("/{user_id}/routes", response_model=list[RouteListItemResponse])
def get_user_routes(
    user_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    repo = RouteRepository(session)
    user_repo = UserRepository(session)
    show_private: bool = False
    if user_repo.has_role(current_user.id, "admin") or user_id == current_user.id:
        show_private = True
    routes = repo.get_by_user(
        target_user_id=user_id,
        show_private=show_private,
        offset=offset,
        limit=limit,
    )
    return [
        RouteListItemResponse(
            id=r.id,
            title=r.title,
            description=r.description,
            created_at=r.created_at,
            created_by=r.created_by,
            is_private=r.is_private,
            likes_count=r.likes_count,
            dislikes_count=r.dislikes_count,
        )
        for r in routes
    ]


@users_router.get("/{user_id}/impressions", response_model=list[ImpressionResponse])
def get_user_impressions(
    user_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    impressions = ImpressionRepository(session).get_by_user(
        user_id=user_id, offset=offset, limit=limit
    )
    return [
        ImpressionResponse(
            id=i.id,
            created_at=i.created_at,
            created_by=i.created_by,
            route_id=i.route_id,
            title=i.title,
            content=i.content,
            likes_count=i.likes_count,
            dislikes_count=i.dislikes_count,
        )
        for i in impressions
    ]
