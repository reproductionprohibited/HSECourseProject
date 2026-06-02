import uuid

from sqlmodel import Session, select

from app.db.models import Impression
from app.repositories.exceptions import NotFoundException


class ImpressionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: uuid.UUID) -> Impression:
        impression = self.session.get(Impression, id)
        if impression is None:
            raise NotFoundException(f"Impression {id} not found")
        return impression

    def get_by_route_id(
        self,
        route_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Impression]:
        query = (
            select(Impression)
            .where(Impression.route_id == route_id)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(query).all())

    def create(
        self,
        created_by: uuid.UUID,
        route_id: uuid.UUID,
        title: str,
        content: str,
    ) -> Impression:
        impression = Impression(
            created_by=created_by,
            route_id=route_id,
            title=title,
            content=content,
        )
        self.session.add(impression)
        self.session.commit()
        self.session.refresh(impression)
        return impression

    def update(
        self,
        impression: Impression,
        title: str | None,
        content: str | None,
    ) -> Impression:
        if title is not None:
            impression.title = title
        if content is not None:
            impression.content = content
        self.session.add(impression)
        self.session.commit()
        self.session.refresh(impression)
        return impression

    def delete(self, impression: Impression) -> None:
        self.session.delete(impression)
        self.session.commit()
