import socket
import threading
import flet as ft
from typing import NoReturn
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

SERVER_PORT = 1234

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
current_username = ""
connected = False  # Tracks if the client is connected to prevent errors


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    return local_ip


def add_message(page: ft.Page, message: str, color: str) -> None:
    message_box.controls.append(ft.Text(message, color=color))
    page.update()


def handle_commands(command: str, page: ft.Page, username_field: ft.TextField):
    if command == "/help":
        add_message(
            page,
            "[INFO] Available commands:\n/help - Show this help\n/username <new_username> - Change your username",
            "yellow",
        )
    elif command.startswith("/username "):
        new_username = command.split("/username ")[1].strip()
        if new_username:
            client.sendall(f"/username {new_username}".encode())
            username_field.value = new_username  # Update input field with new username
        else:
            page.dialog = ft.AlertDialog(
                title=ft.Text("Error: Username cannot be empty")
            )
            page.dialog.open = True
            page.update()
    else:
        add_message(
            page, "[ERROR] Unknown command. Type /help for available commands.", "red"
        )


def connect(
    page: ft.Page, username_field: ft.TextField, join_button: ft.ElevatedButton
) -> None:
    global current_username, connected
    current_username = username_field.value.strip()  # Strip whitespace

    if not current_username:  # Check if the username is empty
        page.dialog = ft.AlertDialog(title=ft.Text("Invalid username: Cannot be empty"))
        page.dialog.open = True
        page.update()
        return  # Prevent further processing if username is empty

    try:
        client.connect((get_local_ip(), SERVER_PORT))
        add_message(page, "[SERVER] Successfully connected to the server!", "blue")
        connected = True  # Set connected to True after a successful connection
    except Exception as e:
        page.dialog = ft.AlertDialog(title=ft.Text(f"Unable to connect to server: {e}"))
        page.dialog.open = True
        page.update()
        return

    client.sendall(current_username.encode())
    threading.Thread(
        target=listen_for_messages_from_server,
        args=(client, page, username_field),
        daemon=True,
    ).start()  # Set the thread as a daemon
    username_field.disabled = True
    join_button.disabled = True
    page.update()


def send_message(
    message_field: ft.TextField, page: ft.Page, username_field: ft.TextField
) -> None:
    global connected
    if not connected:
        page.dialog = ft.AlertDialog(title=ft.Text("You must join the chat first!"))
        page.dialog.open = True
        page.update()
        return

    message = message_field.value.strip()
    if message:
        if message.startswith("/"):
            handle_commands(message, page, username_field)
        else:
            try:
                client.sendall(message.encode())
                add_message(page, f"[You] {message}", color="green")
            except Exception as e:
                page.dialog = ft.AlertDialog(
                    title=ft.Text(f"Error sending message: {e}")
                )
                page.dialog.open = True
                page.update()
        message_field.value = ""
        page.update()
    else:
        page.dialog = ft.AlertDialog(title=ft.Text("Empty message: Cannot be empty"))
        page.dialog.open = True
        page.update()


def listen_for_messages_from_server(
    client: socket.socket, page: ft.Page, username_field: ft.TextField
) -> NoReturn:
    global current_username
    while True:
        try:
            message = client.recv(2048).decode("utf-8")
            if message:
                if message.startswith("SERVER~"):
                    # Display server notifications in blue
                    add_message(page, message.replace("SERVER~", ""), color="blue")
                elif message.startswith("USERNAME_UPDATE~"):
                    _, old_username, new_username = message.split("~")
                    add_message(
                        page,
                        f"[SERVER] {old_username} changed username to {new_username}",
                        "blue",
                    )
                    if old_username == current_username:
                        current_username = new_username
                        username_field.value = new_username  # Update the input field
                        page.update()
                else:
                    username, content = message.split("~")
                    color = "blue" if username == "SERVER" else "white"
                    if username != current_username:
                        add_message(page, f"[{username}] {content}", color)
            else:
                page.dialog = ft.AlertDialog(
                    title=ft.Text("Error: Received empty message")
                )
                page.dialog.open = True
                page.update()
        except Exception as e:
            print(f"Error in message receiving: {e}")
            break


def setup_flet(page: ft.Page) -> None:
    page.title = "Flet Messenger Client"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.scroll = "adaptive"

    # Set up UI with percentage-based widths
    container_width = page.width * 0.8
    button_height = page.height * 0.06
    chat_height = page.height * 0.70
    input_height = page.height * 0.08

    username_field = ft.TextField(
        hint_text="Enter your username",
        width=container_width * 0.8,
        height=input_height,
        text_align="center",
        bgcolor="#1A1A1A",
    )
    join_button = ft.ElevatedButton(
        "Join",
        on_click=lambda _: connect(page, username_field, join_button),
        width=container_width * 0.2,
        height=button_height,
        icon=ft.icons.LOGIN,
    )

    global message_box
    message_box = ft.Column(scroll="auto", expand=True)
    chat_display = ft.Container(
        content=message_box,
        width=container_width,
        height=chat_height,
        bgcolor="#1F1B24",
        border_radius=10,
        padding=ft.Padding(left=10, right=10, top=10, bottom=10),
    )

    message_field = ft.TextField(
        hint_text="Enter your message",
        width=container_width * 0.8,
        height=input_height,
        bgcolor="#1A1A1A",
    )

    send_button = ft.ElevatedButton(
        "Send",
        on_click=lambda _: send_message(message_field, page, username_field),
        width=container_width * 0.2,
        height=button_height,
        icon=ft.icons.SEND,
    )

    page.add(
        ft.Container(
            content=ft.Row([username_field, join_button], alignment="center"),
            padding=ft.Padding(0, 50, 0, 0),
            bgcolor="#121212",
            width=container_width,
        ),
        ft.Container(content=chat_display, width=container_width),
        ft.Container(
            content=ft.Row([message_field, send_button], alignment="center"),
            padding=ft.Padding(0, 0, 0, 20),
            bgcolor="#121212",
            width=container_width,
        ),
    )


def main() -> None:
    ft.app(target=setup_flet)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        client.close()
        print("Client closed")
        exit(0)
