# app/cli/manage.py

import argparse

from sqlmodel import select

from app.user.password import PasswordService
from app.db.engine import sync_session
from app.db.models import Role, UserRoleLink
from app.repositories.user import UserRepository


def create_admin(username: str, password: str):
    with sync_session() as session:
        repo = UserRepository(session)

        try:
            repo.get_by_username(username)
            print(f"User '{username}' already exists")
            return
        except Exception:
            pass

        user = repo.create(
            username=username,
            password_hash=PasswordService.hash_password(password),
        )

        role = session.exec(select(Role).where(Role.name == "admin")).first()

        if role is None:
            role = Role(name="admin")
            session.add(role)
            session.flush()

        session.add(
            UserRoleLink(
                user_id=user.id,
                role_id=role.id,
            )
        )

        session.commit()

        print(f"Admin '{username}' created")


def grant_role(username: str, role_name: str):
    with sync_session() as session:
        repo = UserRepository(session)

        user = repo.get_by_username(username)

        role = session.exec(select(Role).where(Role.name == role_name)).first()

        if role is None:
            role = Role(name=role_name)
            session.add(role)
            session.flush()

        existing = session.exec(
            select(UserRoleLink).where(
                UserRoleLink.user_id == user.id,
                UserRoleLink.role_id == role.id,
            )
        ).first()

        if existing:
            print("Role already granted")
            return

        session.add(
            UserRoleLink(
                user_id=user.id,
                role_id=role.id,
            )
        )

        session.commit()

        print(f"Granted role '{role_name}' to '{username}'")


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")

    create_admin_parser = subparsers.add_parser("create-admin")
    create_admin_parser.add_argument("username")
    create_admin_parser.add_argument("password")

    grant_role_parser = subparsers.add_parser("grant-role")
    grant_role_parser.add_argument("username")
    grant_role_parser.add_argument("role")

    args = parser.parse_args()

    if args.command == "create-admin":
        create_admin(args.username, args.password)

    elif args.command == "grant-role":
        grant_role(args.username, args.role)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
