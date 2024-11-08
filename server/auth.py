import bcrypt
from database import SessionLocal, User
from flask import request, jsonify, Response
from typing import Literal
import base64


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    encoded_hash = base64.b64encode(hashed).decode("utf-8")
    return encoded_hash


def verify_password(stored_password: str, provided_password: str) -> bool:
    hashed_password_bytes = base64.b64decode(stored_password.encode("utf-8"))
    return bcrypt.checkpw(provided_password.encode("utf-8"), hashed_password_bytes)


def register_user(username: str, password: str) -> User:
    """Register a new user."""
    with SessionLocal() as session:
        if session.query(User).filter_by(username=username).first():
            raise ValueError("Username already exists.")

        hashed_password = hash_password(password)
        new_user = User(username=username, password_hash=hashed_password)
        session.add(new_user)
        session.commit()

        session.refresh(new_user)
        return new_user


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate user credentials."""
    with SessionLocal() as session:
        user = session.query(User).filter_by(username=username).first()
        if user and verify_password(user.password_hash, password):
            return user
        return None
