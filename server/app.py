from dotenv import load_dotenv

load_dotenv()
from typing import Literal
from flask import Flask, Response, request, jsonify
from flasgger import Swagger
from auth import register_user, authenticate_user
from room import create_room, join_room, get_public_rooms, get_room
from message import send_message, get_room_messages
from database import SessionLocal, User

app = Flask(__name__)
swagger = Swagger(app, template_file="../swagger.yaml")


@app.route("/")
def index() -> Response:
    return jsonify({"message": "Hello, World!"})


@app.route("/register", methods=["POST"])
def register() -> tuple[Response, Literal[201]] | tuple[Response, Literal[400]]:
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    try:
        user = register_user(username, password)
        return (
            jsonify(
                {
                    "message": f"User '{username}' registered successfully!",
                    "id": user.id,
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/login", methods=["POST"])
def login() -> tuple[Response, Literal[200]] | tuple[Response, Literal[401]]:
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = authenticate_user(username, password)
    if user:
        return jsonify({"message": "Login successful", "id": user.id}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/rooms", methods=["POST"])
def create_chat_room() -> tuple[Response, Literal[201]] | tuple[Response, Literal[400]]:
    data = request.get_json()
    name = data.get("name")
    admin_id = data.get("admin_id")
    timeout_minutes = data.get("timeout_minutes")
    is_private = data.get("is_private", False)
    access_code = data.get("access_code", None)

    try:
        room = create_room(
            admin_id=admin_id,
            name=name,
            timeout_minutes=timeout_minutes,
            is_private=is_private,
            access_code=access_code,
        )
        return (
            jsonify(
                {
                    "message": f"Room '{room.name}' created successfully",
                    "room_id": room.id,
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/rooms/join", methods=["POST"])
def join_chat_room() -> tuple[Response, Literal[200]] | tuple[Response, Literal[400]]:
    data = request.get_json()
    user_id = data.get("user_id")
    room_id = data.get("room_id")
    access_code = data.get("access_code", None)

    try:
        room = join_room(user_id, room_id, access_code)
        if not room:
            return jsonify({"error": "Failed to join room"}), 400
        return jsonify({"message": f"Joined room with ID {room_id}"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/rooms", methods=["GET"])
def list_public_rooms() -> tuple[Response, Literal[200]]:
    rooms = get_public_rooms()
    room_list = [
        {"id": room.id, "name": room.name, "admin_id": room.admin_id} for room in rooms
    ]
    return jsonify(room_list), 200


@app.route("/rooms/<int:room_id>", methods=["GET"])
def get_chat_room(
    room_id: int,
) -> tuple[Response, Literal[200]] | tuple[Response, Literal[404]]:
    room = get_room(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    return (
        jsonify(
            {
                "id": room.id,
                "name": room.name,
                "admin_id": room.admin_id,
                "port": room.port,
            }
        ),
        200,
    )


@app.route("/rooms/<int:room_id>/messages", methods=["POST"])
def post_message(
    room_id: int,
) -> (
    tuple[Response, Literal[404]]
    | tuple[Response, Literal[201]]
    | tuple[Response, Literal[400]]
):
    data = request.get_json()
    user_id = data.get("user_id")
    content = data.get("content")

    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

    try:
        message_data = send_message(user, room_id, content)
        return (
            jsonify({"message": "Message sent", "content": message_data["content"]}),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/rooms/<int:room_id>/messages", methods=["GET"])
def get_messages(room_id: int) -> tuple[Response, Literal[200]]:
    messages = get_room_messages(room_id)
    message_list = [
        {
            "username": message.user.username,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
        }
        for message in messages
    ]
    return jsonify(message_list), 200


if __name__ == "__main__":
    app.run(debug=True)
