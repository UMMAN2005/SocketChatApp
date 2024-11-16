import threading
from database import Room, RoomAccess, User, SessionLocal
from typing import Optional
import socket
from server import start_room_server


def get_next_available_port(start_port=5000) -> int:
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
        port += 1


def create_room(
    admin_id: int,
    name: str,
    is_private: bool = False,
    access_code: Optional[str] = None,
    timeout_minutes: int = 60,
) -> Room:
    with SessionLocal() as session:
        port = get_next_available_port()
        room = Room(
            name=name,
            is_private=is_private,
            timeout_minutes=timeout_minutes,
            port=port,
            admin_id=admin_id,
        )
        if access_code and is_private:
            room.set_access_code(access_code)

        session.add(room)
        session.commit()
        session.refresh(room)

        room_access = RoomAccess(room_id=room.id, user_id=admin_id, can_join=True)
        session.add(room_access)
        session.commit()

        threading.Thread(target=start_room_server, args=(room.port,)).start()

        print(
            f"Room '{name}' created with ID: {room.id}, port: {port}, and timeout: {timeout_minutes} mins."
        )
        return room


def join_room(
    user_id: int, room_id: int, access_code: Optional[str] = None
) -> Optional[Room]:
    """Allows a user to join a room if they have permission or the correct access code."""
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        room = session.query(Room).filter(Room.id == room_id).first()

        if not room:
            print("Room does not exist.")
            return None

        if not room.is_active():
            print("Room has timed out.")
            return None

        if room.is_private and not room.check_access_code(access_code or ""):
            print("Incorrect access code for private room.")
            return None

        room_access = (
            session.query(RoomAccess)
            .filter(RoomAccess.room_id == room_id, RoomAccess.user_id == user_id)
            .first()
        )

        if not room_access:
            room_access = RoomAccess(room_id=room_id, user_id=user_id, can_join=True)
            session.add(room_access)
            session.commit()

        print(f"User '{user.username}' joined room '{room.name}'.")
        return room


def get_public_rooms() -> list[Room]:
    """Retrieves all active public rooms."""
    with SessionLocal() as session:
        rooms = session.query(Room).filter(Room.is_private == False).all()
        print(f"Found {len(rooms)} public rooms.")
        active_rooms = [room for room in rooms if room.is_active()]
        print(f"Found {len(active_rooms)} active public rooms.")
        return active_rooms


def get_room(room_id: int) -> Optional[Room]:
    with SessionLocal() as session:
        room = session.query(Room).filter(Room.id == room_id).first()
        if room:
            print(f"Found room '{room.name}' with ID: {room.id}.")
        return room
