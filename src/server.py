import socket
import threading
from typing import NoReturn
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

HOST = "0.0.0.0"
PORT = 1234
LISTENER_LIMIT = 5
active_clients = []
lock = threading.Lock()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def listen_for_messages(client: socket.socket, username: str) -> None:
    while True:
        try:
            message = client.recv(2048).decode("utf-8")
            if message:
                if message.startswith("/username "):
                    new_username = message.split(" ", 1)[1]
                    update_username(client, username, new_username)
                    username = new_username
                else:
                    final_msg = username + "~" + message
                    send_messages_to_all(final_msg)
            else:
                remove_client(client)
                break
        except:
            remove_client(client)
            break


def update_username(
    client: socket.socket, old_username: str, new_username: str
) -> None:
    with lock:
        for idx, (username, client_socket) in enumerate(active_clients):
            if client_socket == client:
                active_clients[idx] = (new_username, client)
                break
    notification = f"SERVER~{old_username} changed their name to {new_username}"
    send_messages_to_all(notification)


def send_message_to_client(client: socket.socket, message: str) -> None:
    client.sendall(message.encode())


def send_messages_to_all(message: str) -> None:
    with lock:
        for user in active_clients:
            try:
                send_message_to_client(user[1], message)
            except:
                remove_client(user[1])


def remove_client(client: socket.socket) -> None:
    with lock:
        for user in active_clients:
            if user[1] == client:
                active_clients.remove(user)
                break
        client.close()


def client_handler(client: socket.socket) -> None:
    while True:
        try:
            username = client.recv(2048).decode("utf-8")
            if username:
                with lock:
                    active_clients.append((username, client))
                prompt_message = "SERVER~" + f"{username} joined the chat!"
                send_messages_to_all(prompt_message)
                break
            else:
                print("Client username is empty")
        except:
            remove_client(client)
            return

    threading.Thread(target=listen_for_messages, args=(client, username)).start()


def main() -> NoReturn:
    try:
        server.bind((HOST, PORT))
        print(f"Running the server on {HOST} {PORT}")
    except Exception as e:
        print(f"Unable to bind to host {HOST} and port {PORT}: {e}")
        return

    server.listen(LISTENER_LIMIT)

    while True:
        client, address = server.accept()
        print(f"Successfully connected to client {address[0]} {address[1]}")
        threading.Thread(target=client_handler, args=(client,)).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Server shutting down")
        server.close()
        exit(0)
