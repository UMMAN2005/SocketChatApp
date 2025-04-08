from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime, timedelta
import bcrypt
import os

PASSWORD = os.getenv("PASSWORD")
if PASSWORD is None:
    raise ValueError("PASSWORD is not set in environment variables.")

DATABASE_URI = f"postgresql://postgres:{PASSWORD}@localhost/chat_app"

engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(bind=engine)
Base: DeclarativeMeta = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    messages = relationship("Message", back_populates="user")
    rooms = relationship("Room", back_populates="admin")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    is_private = Column(Boolean, default=False)
    access_code_hash = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    timeout_minutes = Column(Integer, default=60)
    admin_id = Column(Integer, ForeignKey("users.id"))
    port = Column(Integer, nullable=False)

    messages = relationship("Message", back_populates="room")
    admin = relationship("User", back_populates="rooms")

    def set_access_code(self, access_code: str) -> None:
        """Set access code with hashing for private rooms."""
        if access_code:
            self.access_code_hash = bcrypt.hashpw(
                access_code.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

    def check_access_code(self, access_code: str) -> bool:
        """Verify access code for joining a private room."""
        return bcrypt.checkpw(
            access_code.encode("utf-8"), self.access_code_hash.encode("utf-8")
        )

    def is_active(self) -> bool:
        """Check if the room is still within its active timeout."""
        expiration_time = self.created_at + timedelta(minutes=self.timeout_minutes)
        return datetime.now() < expiration_time


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))

    user = relationship("User", back_populates="messages")
    room = relationship("Room", back_populates="messages")


class RoomAccess(Base):
    __tablename__ = "room_access"

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    can_join = Column(Boolean, default=True)

    room = relationship("Room")
    user = relationship("User")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
