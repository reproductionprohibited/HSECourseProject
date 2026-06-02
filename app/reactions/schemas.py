import uuid
from datetime import datetime

from pydantic import BaseModel

from app.db.models import ReactionType, TargetType


class CreateReactionRequest(BaseModel):
    target_id: uuid.UUID
    target_type: TargetType
    type: ReactionType


class ReactionResponse(BaseModel):
    id: uuid.UUID
    target_id: uuid.UUID
    target_type: TargetType
    type: ReactionType
    created_by: uuid.UUID
    created_at: datetime


class RouteReactionsResponse(BaseModel):
    reactions: list[ReactionResponse]
    likes: int
    dislikes: int
