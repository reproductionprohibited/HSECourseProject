import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session

from app.repositories.user import UserRepository
from app.user.utils import get_user, bearer_schema
from app.db.engine import sync_session
from app.impressions.schemas import (
    CreateImpressionRequest,
    ImpressionResponse,
    UpdateImpressionRequest,
)
from app.repositories.exceptions import NotFoundException
from app.repositories.impression import ImpressionRepository
from app.repositories.route import RouteRepository

router = APIRouter(prefix="/impressions", tags=["impressions"])


def get_session():
    with sync_session() as session:
        yield session


def _impression_to_response(impression) -> ImpressionResponse:
    return ImpressionResponse(
        id=impression.id,
        created_at=impression.created_at,
        created_by=impression.created_by,
        route_id=impression.route_id,
        title=impression.title,
        content=impression.content,
        likes_count=impression.likes_count,
        dislikes_count=impression.dislikes_count,
    )


@router.post("", response_model=ImpressionResponse, status_code=HTTPStatus.CREATED)
def create_impression(
    body: CreateImpressionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)

    try:
        RouteRepository(session).get_by_id(body.route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    impression = ImpressionRepository(session).create(
        created_by=current_user.id,
        route_id=body.route_id,
        title=body.title,
        content=body.content,
    )
    return _impression_to_response(impression)


@router.get("/{impression_id}", response_model=ImpressionResponse)
def get_impression(
    impression_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    try:
        impression = ImpressionRepository(session).get_by_id(impression_id)
    except NotFoundException:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Impression not found"
        )

    return _impression_to_response(impression)


@router.put("/{impression_id}", response_model=ImpressionResponse)
def update_impression(
    impression_id: uuid.UUID,
    body: UpdateImpressionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    user_repo = UserRepository(session)

    try:
        impression = ImpressionRepository(session).get_by_id(impression_id)
    except NotFoundException:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Impression not found"
        )

    if impression.created_by != current_user.id and not user_repo.has_role(
        current_user.id, "admin"
    ):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    impression = ImpressionRepository(session).update(
        impression, title=body.title, content=body.content
    )
    return _impression_to_response(impression)


@router.delete("/{impression_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_impression(
    impression_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    user_repo = UserRepository(session)

    try:
        impression = ImpressionRepository(session).get_by_id(impression_id)
    except NotFoundException:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Impression not found"
        )

    if impression.created_by != current_user.id and not user_repo.has_role(
        current_user.id, "admin"
    ):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    ImpressionRepository(session).delete(impression)
