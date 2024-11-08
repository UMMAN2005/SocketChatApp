from typing import List
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from database import Message, User, Room, SessionLocal
import os
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if ENCRYPTION_KEY is None:
    raise ValueError("ENCRYPTION_KEY is not set in environment variables.")


cipher = Fernet(ENCRYPTION_KEY.encode())


def encrypt_message(content: str) -> str:
    return cipher.encrypt(content.encode()).decode()


def decrypt_message(encrypted_content: str) -> str:
    return cipher.decrypt(encrypted_content.encode()).decode()


def send_message(user: User, room_id: int, content: str) -> Message:
    encrypted_content = encrypt_message(content)
    with SessionLocal() as session:
        room = session.query(Room).filter_by(id=room_id).first()
        if not room:
            raise ValueError("Room not found.")

        message = Message(content=encrypted_content, room_id=room.id, user_id=user.id)
        session.add(message)
        session.commit()

        decrypted_content = decrypt_message(message.content)

        return {"content": decrypted_content, "user_id": user.id, "room_id": room.id}


def get_room_messages(room_id: int) -> List[Message]:
    with SessionLocal() as session:
        messages = (
            session.query(Message)
            .filter_by(room_id=room_id)
            .options(joinedload(Message.user))
            .all()
        )
        for message in messages:
            message.content = decrypt_message(message.content)
        return messages
