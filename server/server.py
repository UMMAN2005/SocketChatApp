import socket
import threading
from typing import NoReturn
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

LISTENER_LIMIT = 5
HOST = "0.0.0.0"
room_clients = {}
lock = threading.Lock()


def start_room_server(port: int) -> None:
    room_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    room_server.bind((HOST, port))
    room_server.listen(LISTENER_LIMIT)
    print(f"Room server started on port {port}")

    room_clients[port] = []

    while True:
        client, address = room_server.accept()
        print(f"Client connected to room on port {port}: {address[0]}:{address[1]}")
        threading.Thread(target=handle_room_client, args=(client, port)).start()


def handle_room_client(client: socket.socket, room_port: int) -> None:
    """Handles messages for a client in a specific room."""
    try:
        username = client.recv(2048).decode("utf-8")
        if username:
            with lock:
                room_clients[room_port].append((username, client))
            prompt_message = f"SERVER~{username} joined the room on port {room_port}!"
            send_messages_to_room(prompt_message, room_port)

        listen_for_room_messages(client, username, room_port)

    except Exception as e:
        print(f"Error handling client in room on port {room_port}: {e}")
        remove_client(client)


def listen_for_room_messages(
    client: socket.socket, username: str, room_port: int
) -> None:
    while True:
        try:
            message = client.recv(2048).decode("utf-8")
            if message:
                print(
                    f"Received message from {username} in room on port {room_port}: {message}"
                )
                final_msg = f"{username}~{message}"
                send_messages_to_room(final_msg, room_port)
            else:
                remove_client(client)
                break
        except:
            remove_client(client)
            break


def send_messages_to_room(message: str, room_port: int) -> None:
    """Send a message to all clients in a specific room."""
    with lock:
        for user in room_clients[room_port]:
            try:
                if user[1].getsockname()[1] == room_port:
                    send_message_to_client(user[1], message)
            except:
                remove_client(user[1], room_port)


def send_message_to_client(client: socket.socket, message: str) -> None:
    client.sendall(message.encode())


def remove_client(client: socket.socket, room_port: int) -> None:
    with lock:
        for user in room_clients[room_port]:
            if user[1] == client:
                room_clients[room_port].remove(user)
                break
        client.close()
