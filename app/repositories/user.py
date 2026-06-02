import uuid
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.db.models import User, Role, UserRoleLink
from app.repositories.exceptions import NotFoundException


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: uuid.UUID) -> User:
        user = self.session.get(User, id)
        if user is None:
            raise NotFoundException(f"User {id} not found")
        return user

    def get_by_username(self, username: str) -> User:
        user = self.session.exec(select(User).where(User.username == username)).first()
        if user is None:
            raise NotFoundException(f"User with username '{username}' not found")
        return user

    def create(self, username: str, password_hash: str) -> User:
        user = User(username=username, password_hash=password_hash)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_last_login(self, user: User) -> User:
        user.last_login_at = datetime.now(timezone.utc)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def increment_token_version(self, user: User) -> User:
        user.token_version += 1
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(self, user: User, username: str) -> User:
        user.username = username
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_password(self, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def has_role(self, user_id: uuid.UUID, role_name: str) -> bool:
        query = (
            select(Role)
            .join(UserRoleLink, UserRoleLink.role_id == Role.id)
            .where(UserRoleLink.user_id == user_id)
            .where(Role.name == role_name)
        )
        return self.session.exec(query).first() is not None
