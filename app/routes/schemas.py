import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateRouteRequest(BaseModel):
    title: str
    description: str = ""
    is_private: bool = True


class UpdateRouteRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class CreateRoutePointRequest(BaseModel):
    latitude: float
    longitude: float


class UpdateRoutePointRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ChangePrivacyRequest(BaseModel):
    is_private: bool


class RoutePointResponse(BaseModel):
    id: uuid.UUID
    latitude: float
    longitude: float


class RouteListItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    created_at: datetime
    created_by: uuid.UUID
    is_private: bool
    likes_count: int
    dislikes_count: int


class RouteResponse(RouteListItemResponse):
    points: list[RoutePointResponse]
