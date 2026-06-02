import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateImpressionRequest(BaseModel):
    route_id: uuid.UUID
    title: str
    content: str


class UpdateImpressionRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ImpressionResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    created_by: uuid.UUID
    route_id: uuid.UUID
    title: str
    content: str
    likes_count: int
    dislikes_count: int
