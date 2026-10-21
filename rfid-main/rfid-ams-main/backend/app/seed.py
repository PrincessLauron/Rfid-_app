import os
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .db import SessionLocal, engine
from . import models

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def seed_roles(db: Session) -> dict[str, models.Role]:
    role_names = [
        ("admin", "Full administrative access"),
        ("technician", "Can manage assets and perform scans"),
        ("viewer", "Read-only access"),
    ]
    existing = {r.name: r for r in db.query(models.Role).all()}
    roles: dict[str, models.Role] = {}
    for name, description in role_names:
        if name in existing:
            roles[name] = existing[name]
            continue
        role = models.Role(name=name, description=description)
        db.add(role)
        db.flush()
        roles[name] = role
    return roles


def seed_admin(db: Session, roles: dict[str, models.Role]) -> models.User:
    admin_username = os.getenv("AMS_ADMIN_USERNAME", "admin")
    admin_email = os.getenv("AMS_ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("AMS_ADMIN_PASSWORD", "admin123")

    user = db.query(models.User).filter(
        (models.User.username == admin_username) | (models.User.email == admin_email)
    ).first()
    if user:
        # ensure admin role attached
        if roles["admin"] not in user.roles:
            user.roles.append(roles["admin"])
        return user

    user = models.User(
        username=admin_username,
        email=admin_email,
        password_hash=get_password_hash(admin_password),
        is_active=True,
    )
    user.roles.append(roles["admin"])
    db.add(user)
    return user


def seed_rooms(db: Session) -> None:
    default_rooms = [
        ("IOT Laboratory", "IOT"),
        ("Network Laboratory", "NET"),
        ("Embedded Laboratory", "EMB"),
        ("Multimedia Laboratory", "MMD"),
        ("Database Lab", "DB"),
        ("CS Lab", "CS"),
    ]
    existing_by_name = {r.name for r in db.query(models.Room).all()}
    for name, code in default_rooms:
        if name in existing_by_name:
            continue
        db.add(models.Room(name=name, code=code))


def run() -> None:
    # Ensure tables exist (in case migrations not applied)
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        roles = seed_roles(db)
        seed_admin(db, roles)
        seed_rooms(db)
        db.commit()
        print("Seed complete.")
    except Exception as exc:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()

