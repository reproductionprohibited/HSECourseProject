import uuid

from sqlmodel import Session, select

from app.db.models import Reaction, ReactionType, TargetType
from app.repositories.exceptions import NotFoundException


class ReactionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: uuid.UUID) -> Reaction:
        reaction = self.session.get(Reaction, id)
        if reaction is None:
            raise NotFoundException(f"Reaction {id} not found")
        return reaction

    def get_by_user_and_target(
        self,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: TargetType,
    ) -> Reaction | None:
        query = (
            select(Reaction)
            .where(Reaction.created_by == user_id)
            .where(Reaction.target_id == target_id)
            .where(Reaction.target_type == target_type)
        )
        return self.session.exec(query).first()

    def get_by_target(
        self,
        target_id: uuid.UUID,
        target_type: TargetType,
    ) -> list[Reaction]:
        query = (
            select(Reaction)
            .where(Reaction.target_id == target_id)
            .where(Reaction.target_type == target_type)
        )
        return list(self.session.exec(query).all())

    def create(
        self,
        created_by: uuid.UUID,
        target_id: uuid.UUID,
        target_type: TargetType,
        type: ReactionType,
    ) -> Reaction:
        reaction = Reaction(
            created_by=created_by,
            target_id=target_id,
            target_type=target_type,
            type=type,
        )
        self.session.add(reaction)
        self.session.commit()
        self.session.refresh(reaction)
        return reaction

    def update_type(self, reaction: Reaction, type: ReactionType) -> Reaction:
        reaction.type = type
        self.session.add(reaction)
        self.session.commit()
        self.session.refresh(reaction)
        return reaction

    def delete(self, reaction: Reaction) -> None:
        self.session.delete(reaction)
        self.session.commit()
