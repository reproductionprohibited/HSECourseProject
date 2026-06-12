import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session

from app.user.utils import get_user, bearer_schema
from app.db.engine import sync_session
from app.db.models import TargetType
from app.reactions.schemas import CreateReactionRequest, ReactionResponse
from app.repositories.exceptions import NotFoundException
from app.repositories.impression import ImpressionRepository
from app.repositories.reaction import ReactionRepository
from app.repositories.route import RouteRepository

router = APIRouter(prefix="/reactions", tags=["reactions"])


def get_session():
    with sync_session() as session:
        yield session


def _reaction_to_response(reaction) -> ReactionResponse:
    return ReactionResponse(
        id=reaction.id,
        target_id=reaction.target_id,
        target_type=reaction.target_type,
        type=reaction.type,
        created_by=reaction.created_by,
        created_at=reaction.created_at,
    )


@router.post("", response_model=ReactionResponse, status_code=HTTPStatus.OK)
def create_reaction(
    body: CreateReactionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    try:
        if body.target_type == TargetType.route:
            RouteRepository(session).get_by_id(body.target_id)
        else:
            ImpressionRepository(session).get_by_id(body.target_id)

    except NotFoundException:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Target not found",
        )

    repo = ReactionRepository(session)

    existing = repo.get_by_user_and_target(
        user_id=current_user.id,
        target_id=body.target_id,
        target_type=body.target_type,
    )

    if existing is not None:
        if existing.type == body.type:
            return _reaction_to_response(existing)
        reaction = repo.update_type(existing, type=body.type)
        _update_counts(session, body.target_id, body.target_type)
        return _reaction_to_response(reaction)

    reaction = repo.create(
        created_by=current_user.id,
        target_id=body.target_id,
        target_type=body.target_type,
        type=body.type,
    )
    _update_counts(session, body.target_id, body.target_type)
    return _reaction_to_response(reaction)


@router.delete("/{reaction_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_reaction(
    reaction_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    session: Session = Depends(get_session),
):
    current_user = get_user(session, credentials.credentials)
    repo = ReactionRepository(session)

    try:
        reaction = repo.get_by_id(reaction_id)
    except NotFoundException:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Reaction not found"
        )

    if reaction.created_by != current_user.id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Access denied")

    repo.delete(reaction)
    _update_counts(session, reaction.target_id, reaction.target_type)


def _update_counts(
    session: Session, target_id: uuid.UUID, target_type: TargetType
) -> None:
    from app.db.models import ReactionType

    reactions = ReactionRepository(session).get_by_target(target_id, target_type)
    likes = sum(1 for r in reactions if r.type == ReactionType.like)
    dislikes = sum(1 for r in reactions if r.type == ReactionType.dislike)

    if target_type == TargetType.route:
        try:
            route = RouteRepository(session).get_by_id(target_id)
            route.likes_count = likes
            route.dislikes_count = dislikes
            session.add(route)
            session.commit()
        except NotFoundException:
            pass
    else:
        try:
            impression = ImpressionRepository(session).get_by_id(target_id)
            impression.likes_count = likes
            impression.dislikes_count = dislikes
            session.add(impression)
            session.commit()
        except NotFoundException:
            pass
