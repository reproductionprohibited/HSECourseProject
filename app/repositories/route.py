import uuid

from sqlmodel import Session, select

from app.db.models import Route, RoutePoint, RoutePointLink
from app.repositories.exceptions import NotFoundException


class RouteRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_public(
        self,
        offset: int = 0,
        limit: int = 20,
        title: str | None = None,
        created_by: uuid.UUID | None = None,
    ) -> list[Route]:
        query = select(Route).where(Route.is_private == False)  # noqa: E712
        if title is not None:
            query = query.where(Route.title.ilike(f"%{title}%"))
        if created_by is not None:
            query = query.where(Route.created_by == created_by)
        query = query.offset(offset).limit(limit)
        return list(self.session.exec(query).all())

    def get_by_id(self, id: uuid.UUID) -> Route:
        route = self.session.get(Route, id)
        if route is None:
            raise NotFoundException(f"Route {id} not found")
        return route

    def create(
        self, created_by: uuid.UUID, title: str, description: str, is_private: bool
    ) -> Route:
        route = Route(
            created_by=created_by,
            title=title,
            description=description,
            is_private=is_private,
        )
        self.session.add(route)
        self.session.commit()
        self.session.refresh(route)
        return route

    def update(self, route: Route, title: str | None, description: str | None) -> Route:
        if title is not None:
            route.title = title
        if description is not None:
            route.description = description
        self.session.add(route)
        self.session.commit()
        self.session.refresh(route)
        return route

    def delete(self, route: Route) -> None:
        self.session.delete(route)
        self.session.commit()

    def change_privacy(self, route: Route, is_private: bool) -> Route:
        route.is_private = is_private
        self.session.add(route)
        self.session.commit()
        self.session.refresh(route)
        return route

    def get_points(self, route_id: uuid.UUID) -> list[RoutePoint]:
        query = (
            select(RoutePoint)
            .join(RoutePointLink, RoutePointLink.point_id == RoutePoint.id)
            .where(RoutePointLink.route_id == route_id)
        )
        return list(self.session.exec(query).all())

    def search_by_point(
        self, latitude: float, longitude: float, delta: float = 0.001
    ) -> list[Route]:
        query = (
            select(Route)
            .join(RoutePointLink, RoutePointLink.route_id == Route.id)
            .join(RoutePoint, RoutePoint.id == RoutePointLink.point_id)
            .where(Route.is_private == False)  # noqa: E712
            .where(RoutePoint.latitude.between(latitude - delta, latitude + delta))
            .where(RoutePoint.longitude.between(longitude - delta, longitude + delta))
        )
        return list(self.session.exec(query).all())


class RoutePointRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id: uuid.UUID) -> RoutePoint:
        point = self.session.get(RoutePoint, id)
        if point is None:
            raise NotFoundException(f"RoutePoint {id} not found")
        return point

    def create(
        self, route_id: uuid.UUID, latitude: float, longitude: float
    ) -> RoutePoint:
        point = RoutePoint(latitude=latitude, longitude=longitude)
        self.session.add(point)
        self.session.flush()
        link = RoutePointLink(route_id=route_id, point_id=point.id)
        self.session.add(link)
        self.session.commit()
        self.session.refresh(point)
        return point

    def update(
        self, point: RoutePoint, latitude: float | None, longitude: float | None
    ) -> RoutePoint:
        if latitude is not None:
            point.latitude = latitude
        if longitude is not None:
            point.longitude = longitude
        self.session.add(point)
        self.session.commit()
        self.session.refresh(point)
        return point

    def delete(self, route_id: uuid.UUID, point: RoutePoint) -> None:
        link = self.session.exec(
            select(RoutePointLink)
            .where(RoutePointLink.route_id == route_id)
            .where(RoutePointLink.point_id == point.id)
        ).first()
        if link:
            self.session.delete(link)
            self.session.flush()
        self.session.delete(point)
        self.session.commit()
