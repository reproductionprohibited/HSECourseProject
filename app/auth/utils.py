import uuid
from http import HTTPStatus

from fastapi import HTTPException
from fastapi.security import HTTPBearer
from sqlmodel import Session

from app.auth.jwt import JWTService
from app.db.models import User
from app.repositories.exceptions import NotFoundException
from app.repositories.user import UserRepository


bearer_schema = HTTPBearer()


def get_user(session: Session, token: str) -> User:
    try:
        payload = JWTService.decode(token)
    except Exception:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")

    try:
        user = UserRepository(session).get_by_id(id=uuid.UUID(payload["iss"]))
    except NotFoundException:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")

    if user.token_version != payload["ver"]:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")

    return user
