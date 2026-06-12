import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.user.utils import get_user, bearer_schema
from app.db.engine import sync_session
from app.db.models import User, TargetType, ReactionType
from app.impressions.routes import _impression_to_response
from app.impressions.schemas import ImpressionResponse
from app.reactions.schemas import RouteReactionsResponse, ReactionResponse
from app.repositories.exceptions import NotFoundException
from app.repositories.impression import ImpressionRepository
from app.repositories.reaction import ReactionRepository
from app.repositories.route import RouteRepository, RoutePointRepository
from app.repositories.user import UserRepository
from app.routes.schemas import (
    ChangePrivacyRequest,
    CreateRoutePointRequest,
    CreateRouteRequest,
    RouteListItemResponse,
    RoutePointResponse,
    RouteResponse,
    UpdateRoutePointRequest,
    UpdateRouteRequest,
)

router = APIRouter(prefix="/routes", tags=["routes"])


def get_session():
    with sync_session() as session:
        yield session


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
    session: Session = Depends(get_session),
) -> User | None:
    if credentials is None:
        return None
    return get_user(session, credentials.credentials)


def _route_to_response(route, points) -> RouteResponse:
    return RouteResponse(
        id=route.id,
        title=route.title,
        description=route.description,
        created_at=route.created_at,
        created_by=route.created_by,
        is_private=route.is_private,
        likes_count=route.likes_count,
        dislikes_count=route.dislikes_count,
        points=[
            RoutePointResponse(id=p.id, latitude=p.latitude, longitude=p.longitude)
            for p in points
        ],
    )


@router.get("", response_model=list[RouteListItemResponse])
def get_routes(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    title: str | None = Query(default=None),
    created_by: uuid.UUID | None = Query(default=None),
    session: Session = Depends(get_session),
):
    repo = RouteRepository(session)
    routes = repo.get_all_public(
        offset=offset, limit=limit, title=title, created_by=created_by
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


@router.post("", response_model=RouteResponse, status_code=HTTPStatus.CREATED)
def create_route(
    body: CreateRouteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)

    if not body.is_private:
        if not UserRepository(session).has_role(current_user.id, "route_creator"):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Only route creators can create public routes",
            )

    route = RouteRepository(session).create(
        created_by=current_user.id,
        title=body.title,
        description=body.description,
        is_private=body.is_private,
    )
    return _route_to_response(route, [])


@router.get("/search/by-point", response_model=list[RouteListItemResponse])
def search_by_point(
    lat: float = Query(),
    lng: float = Query(),
    session: Session = Depends(get_session),
):
    routes = RouteRepository(session).search_by_point(latitude=lat, longitude=lng)
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


@router.get("/{route_id}", response_model=RouteResponse)
def get_route(
    route_id: uuid.UUID,
    current_user: User | None = Depends(optional_user),
    session: Session = Depends(get_session),
):
    repo = RouteRepository(session)
    try:
        route = repo.get_by_id(route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    if route.is_private and (
        current_user is None or route.created_by != current_user.id
    ):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    points = repo.get_points(route_id)
    return _route_to_response(route, points)


@router.put("/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: uuid.UUID,
    body: UpdateRouteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    repo = RouteRepository(session)

    try:
        route = repo.get_by_id(route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    if route.created_by != current_user.id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    route = repo.update(route, title=body.title, description=body.description)
    points = repo.get_points(route_id)
    return _route_to_response(route, points)


@router.delete("/{route_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_route(
    route_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    repo = RouteRepository(session)

    try:
        route = repo.get_by_id(route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    if route.created_by != current_user.id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    repo.delete(route)


@router.patch("/{route_id}/privacy", response_model=RouteResponse)
def change_privacy(
    route_id: uuid.UUID,
    body: ChangePrivacyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)

    if not UserRepository(session).has_role(current_user.id, "route_creator"):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Only route creators can change privacy",
        )

    repo = RouteRepository(session)
    try:
        route = repo.get_by_id(route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    if route.created_by != current_user.id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    route = repo.change_privacy(route, is_private=body.is_private)
    points = repo.get_points(route_id)
    return _route_to_response(route, points)


@router.post(
    "/{route_id}/points",
    response_model=RoutePointResponse,
    status_code=HTTPStatus.CREATED,
)
def add_point(
    route_id: uuid.UUID,
    body: CreateRoutePointRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    repo = RouteRepository(session)

    try:
        route = repo.get_by_id(route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    if route.created_by != current_user.id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    point = RoutePointRepository(session).create(
        route_id=route_id, latitude=body.latitude, longitude=body.longitude
    )
    return RoutePointResponse(
        id=point.id, latitude=point.latitude, longitude=point.longitude
    )


@router.put("/{route_id}/points/{point_id}", response_model=RoutePointResponse)
def update_point(
    route_id: uuid.UUID,
    point_id: uuid.UUID,
    body: UpdateRoutePointRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    repo = RouteRepository(session)

    try:
        route = repo.get_by_id(route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    if route.created_by != current_user.id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    point_repo = RoutePointRepository(session)
    try:
        point = point_repo.get_by_id(point_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Point not found")

    point = point_repo.update(point, latitude=body.latitude, longitude=body.longitude)
    return RoutePointResponse(
        id=point.id, latitude=point.latitude, longitude=point.longitude
    )


@router.delete("/{route_id}/points/{point_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_point(
    route_id: uuid.UUID,
    point_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    repo = RouteRepository(session)

    try:
        route = repo.get_by_id(route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    if route.created_by != current_user.id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    point_repo = RoutePointRepository(session)
    try:
        point = point_repo.get_by_id(point_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Point not found")

    point_repo.delete(route_id=route_id, point=point)


@router.get("/{route_id}/reactions", response_model=RouteReactionsResponse)
def get_route_reactions(
    route_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    try:
        RouteRepository(session).get_by_id(route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    reactions = ReactionRepository(session).get_by_target(route_id, TargetType.route)
    responses = [
        ReactionResponse(
            id=r.id,
            target_id=r.target_id,
            target_type=r.target_type,
            type=r.type,
            created_by=r.created_by,
            created_at=r.created_at,
        )
        for r in reactions
    ]
    return RouteReactionsResponse(
        reactions=responses,
        likes=sum(1 for r in reactions if r.type == ReactionType.like),
        dislikes=sum(1 for r in reactions if r.type == ReactionType.dislike),
    )


@router.get("/{route_id}/impressions", response_model=list[ImpressionResponse])
def get_route_impressions(
    route_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    try:
        RouteRepository(session).get_by_id(route_id)
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Route not found")

    impressions = ImpressionRepository(session).get_by_route_id(
        route_id, offset=offset, limit=limit
    )
    return [_impression_to_response(i) for i in impressions]
