import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class ReactionType(str, Enum):
    like = "like"
    dislike = "dislike"


class TargetType(str, Enum):
    route = "route"
    impression = "impression"


class UserRoleLink(SQLModel, table=True):
    __tablename__ = "user_role_links"

    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    role_id: uuid.UUID = Field(foreign_key="roles.id", primary_key=True)


class RolePermissionLink(SQLModel, table=True):
    __tablename__ = "role_permission_links"

    role_id: uuid.UUID = Field(foreign_key="roles.id", primary_key=True)
    permission_id: uuid.UUID = Field(foreign_key="permissions.id", primary_key=True)


class RoutePointLink(SQLModel, table=True):
    __tablename__ = "route_point_links"

    route_id: uuid.UUID = Field(foreign_key="routes.id", primary_key=True)
    point_id: uuid.UUID = Field(foreign_key="route_points.id", primary_key=True)


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True)
    token_version: int = Field(default=1)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None


class RoutePoint(SQLModel, table=True):
    __tablename__ = "route_points"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    latitude: float
    longitude: float


class Route(SQLModel, table=True):
    __tablename__ = "routes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = Field(foreign_key="users.id")
    is_private: bool = Field(default=True)
    likes_count: int = Field(default=0)
    dislikes_count: int = Field(default=0)


class Impression(SQLModel, table=True):
    __tablename__ = "impressions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = Field(foreign_key="users.id")
    route_id: uuid.UUID = Field(foreign_key="routes.id")
    title: str
    content: str
    likes_count: int = Field(default=0)
    dislikes_count: int = Field(default=0)


class Reaction(SQLModel, table=True):
    __tablename__ = "reactions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    target_id: uuid.UUID = Field(index=True)
    target_type: TargetType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = Field(foreign_key="users.id")
    type: ReactionType
