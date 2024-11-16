import socket
import asyncio
import requests
import threading
import flet as ft
from typing import NoReturn
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

API_BASE_URL = "http://localhost:5000"
SERVER_HOST = "localhost"

current_user_id = None
current_room_id = None
socket_connection = None


def listen_for_messages_from_server(page: ft.Page, message_box: ft.Column) -> None:
    while True:
        try:
            print("Listening for messages...")
            message = socket_connection.recv(1024).decode()
            print(f"Received message: {message}")
            if message:
                sender = message.split("~")[0]
                if sender == "SERVER":
                    content = message.split("~")[1]
                    print(f"Content: {content}")
                else:
                    content = message.split("~")[2]
                print(f"Sender: {sender}, Content: {content}")
                if content:
                    message_box.controls.append(ft.Text(f"{sender}: {content}"))
                    page.update()
        except Exception as e:
            print(f"Error receiving message: {e}")
            break


def show_login_register_ui(page: ft.Page, visible_form: str | None) -> None:
    username_field = ft.TextField(hint_text="Username")
    password_field = ft.TextField(hint_text="Password", password=True)
    confirm_password_field = ft.TextField(
        hint_text="Confirm Password", password=True, visible=False
    )

    async def on_login(_) -> None:
        login_response = login(username_field.value, password_field.value)
        if login_response:
            page.dialog = ft.AlertDialog(
                title=ft.Text("Login Successful"),
                content=ft.Text("Welcome back!"),
                open=True,
            )
            page.update()

            await asyncio.sleep(2)
            page.dialog.open = False
            page.update()

            show_main_menu_ui(page)
        else:
            page.dialog = ft.AlertDialog(
                title=ft.Text("Login Failed"),
                content=ft.Text("Incorrect username or password."),
                open=True,
            )
            page.update()

            await asyncio.sleep(2)
            page.dialog.open = False
            page.update()

            show_login_register_ui(page, "login")

    async def on_register(_) -> None:
        if password_field.value != confirm_password_field.value:
            page.dialog = ft.AlertDialog(
                title=ft.Text("Registration Failed"),
                content=ft.Text("Passwords do not match."),
                open=True,
            )
            page.update()

            await asyncio.sleep(2)
            page.dialog.open = False
            page.update()

            show_login_register_ui(page, "register")
            return

        register_response = register(username_field.value, password_field.value)
        if register_response:
            page.dialog = ft.AlertDialog(
                title=ft.Text("Registration Successful"),
                content=ft.Text("Account created! Please log in."),
                open=True,
            )
            page.update()

            await asyncio.sleep(2)
            page.dialog.open = False
            page.update()

            show_login_register_ui(page, "login")

    register_button = ft.ElevatedButton(
        "Register",
        on_click=on_register,
        visible=True if visible_form == "register" else False,
    )
    login_button = ft.ElevatedButton(
        "Login", on_click=on_login, visible=True if visible_form == "login" else False
    )

    def show_login_form() -> None:
        confirm_password_field.visible = False
        register_button.visible = False
        login_button.visible = True
        page.update()

    def show_register_form() -> None:
        confirm_password_field.visible = True
        register_button.visible = True
        login_button.visible = False
        page.update()

    dialog = ft.AlertDialog(
        title=ft.Text("Login or Register", text_align=ft.TextAlign.CENTER),
        content=ft.Column(
            [
                username_field,
                password_field,
                confirm_password_field,
                ft.Row(
                    [login_button, register_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            height=page.height * 0.5,
        ),
        actions=[
            ft.TextButton("Switch to Login", on_click=lambda _: show_login_form()),
            ft.TextButton(
                "Switch to Register", on_click=lambda _: show_register_form()
            ),
        ],
    )

    page.dialog = dialog
    dialog.open = True
    page.update()


def login(username: str, password: str) -> bool:
    global current_user_id
    response = requests.post(
        f"{API_BASE_URL}/login", json={"username": username, "password": password}
    )
    if response.status_code == 200:
        current_user_id = response.json().get("id")
        return True
    return False


def register(username: str, password: str) -> bool:
    global current_user_id
    response = requests.post(
        f"{API_BASE_URL}/register", json={"username": username, "password": password}
    )
    if response.status_code == 201:
        current_user_id = response.json().get("id")
        return True
    return False


def show_main_menu_ui(page: ft.Page) -> None:
    dialog_content = ft.Column(
        [
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Create New Room",
                        on_click=lambda _: show_create_room_ui(page),
                        height=page.height * 0.1,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    ft.ElevatedButton(
                        "View Rooms",
                        on_click=lambda _: show_public_rooms_ui(page),
                        height=page.height * 0.1,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        height=page.height * 0.5,
    )

    page.dialog = ft.AlertDialog(
        title=ft.Text("Main Menu", text_align=ft.TextAlign.CENTER),
        content=dialog_content,
        actions=[],
    )

    page.dialog.open = True
    page.update()


def show_create_room_ui(page: ft.Page) -> None:
    room_name_field = ft.TextField(hint_text="Room Name")
    timeout_field = ft.TextField(hint_text="Timeout (minutes)")
    access_code_field = ft.TextField(hint_text="Access Code", password=True)

    async def on_create_room(_) -> None:
        create_response = create_room(
            room_name_field.value,
            int(timeout_field.value) if timeout_field.value else 0,
            access_code_field.value,
        )
        if create_response:
            page.dialog = ft.AlertDialog(
                title=ft.Text("Room Created"),
                content=ft.Text("Room created successfully!"),
                open=True,
            )
            page.update()

            await asyncio.sleep(2)
            page.dialog.open = False
            page.update()

            show_create_room_ui(page)

    dialog_content = ft.Column(
        [
            room_name_field,
            timeout_field,
            access_code_field,
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Back",
                        on_click=lambda _: show_main_menu_ui(page),
                    ),
                    ft.ElevatedButton("Create", on_click=on_create_room),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    page.dialog = ft.AlertDialog(
        title=ft.Text("Create Room", text_align=ft.TextAlign.CENTER),
        content=dialog_content,
        actions=[],
    )

    page.dialog.open = True
    page.update()


def show_public_rooms_ui(page: ft.Page) -> None:
    nickname_field = ft.TextField(hint_text="Enter Nickname")

    async def on_join_room(
        _, room_id: int | None, nickname: str, access_code: str | None
    ) -> None:
        if nickname and join_room(room_id, access_code):
            show_chat_ui(page, room_id, nickname)
        else:
            page.dialog = ft.AlertDialog(
                title=ft.Text("Join Room Failed"),
                content=ft.Text("Error joining room. Please try again."),
                open=True,
            )
            page.update()

            await asyncio.sleep(2)
            page.dialog.open = False
            page.update()

            show_public_rooms_ui(page)

    response = requests.get(f"{API_BASE_URL}/rooms")
    if response.status_code == 200:
        rooms = response.json()

        dialog_content = ft.Column(
            [
                nickname_field,
                *[
                    ft.Row(
                        [
                            ft.Text(room["name"], text_align=ft.TextAlign.LEFT),
                            ft.ElevatedButton(
                                "Join",
                                on_click=lambda _, room_id=room["id"]: asyncio.run(
                                    on_join_room(_, room_id, nickname_field.value, None)
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                    for room in rooms
                ],
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            height=page.height * 0.5,
        )

        def open_private_room_dialog(_) -> None:
            access_code_field = ft.TextField(
                hint_text="Enter Access Code", password=True
            )

            private_room_dialog = ft.AlertDialog(
                title=ft.Text("Join Private Room", text_align=ft.TextAlign.CENTER),
                content=ft.Column(
                    [
                        nickname_field,
                        access_code_field,
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "Join",
                                    on_click=lambda _: asyncio.run(
                                        on_join_room(
                                            _,
                                            None,
                                            nickname_field.value,
                                            access_code_field.value,
                                        )
                                    ),
                                ),
                                ft.ElevatedButton(
                                    "Back",
                                    on_click=lambda _: show_public_rooms_ui(page),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    height=page.height * 0.5,
                ),
            )
            page.dialog = private_room_dialog
            private_room_dialog.open = True
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text("Rooms", text_align=ft.TextAlign.CENTER),
            content=dialog_content,
            actions=[
                ft.Row(
                    [
                        ft.TextButton(
                            "Join Private Room", on_click=open_private_room_dialog
                        ),
                        ft.TextButton(
                            "Back", on_click=lambda _: show_main_menu_ui(page)
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ],
        )

        page.dialog.open = True
        page.update()


def show_chat_ui(page: ft.Page, room_id: int, nickname: str) -> None:
    response = requests.get(f"{API_BASE_URL}/rooms/{room_id}")
    if response.status_code == 200:
        room = response.json()
        global socket_connection, current_room_id
        current_room_id = room_id
        socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_connection.connect((SERVER_HOST, room["port"]))

        socket_connection.send(nickname.encode())

        messages = get_chat_messages(room_id)
        message_box = ft.Column(
            [ft.Text(f"{message['content']}") for message in messages],
            scroll="auto",
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        threading.Thread(
            target=listen_for_messages_from_server,
            args=(
                page,
                message_box,
            ),
            daemon=True,
        ).start()

    message_field = ft.TextField(hint_text="Enter Message")

    async def send_message(msg: str) -> None:
        if msg:
            post_message(room_id, current_user_id, msg)
            socket_connection.send(f"{nickname}~{msg}".encode())
            message_field.value = ""
            page.update()

    def on_message_sent(_) -> None:
        message = message_field.value
        if message:
            asyncio.run(send_message(message))

    send_button = ft.Row(
        [
            ft.ElevatedButton("Send", on_click=on_message_sent),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    page.dialog = ft.AlertDialog(
        title=ft.Text("Chat Room", text_align=ft.TextAlign.CENTER),
        content=ft.Column(
            [
                message_box,
                message_field,
                send_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            height=page.height * 0.5,
        ),
        actions=[],
    )

    page.dialog.open = True
    page.update()


def create_room(name: str, timeout_minutes: int, access_code: str) -> bool:
    global current_room_id
    response = requests.post(
        f"{API_BASE_URL}/rooms",
        json={
            "name": name,
            "admin_id": current_user_id,
            "timeout_minutes": timeout_minutes,
            "access_code": access_code,
            "is_private": True if access_code else False,
        },
    )
    if response.status_code == 201:
        current_room_id = response.json().get("room_id")
        return True
    return False


def join_room(room_id: int, access_code: str | None) -> bool:
    global current_room_id
    response = requests.post(
        f"{API_BASE_URL}/rooms/join",
        json={
            "user_id": current_user_id,
            "room_id": room_id,
            "access_code": access_code,
        },
    )
    if response.status_code == 200:
        return True
    return False


def get_chat_messages(room_id: int) -> list[str]:
    response = requests.get(f"{API_BASE_URL}/rooms/{room_id}/messages")
    if response.status_code == 200:
        return response.json()
    return []


def post_message(room_id: int, user_id: int, content: str) -> bool:
    response = requests.post(
        f"{API_BASE_URL}/rooms/{room_id}/messages",
        json={"user_id": user_id, "content": content},
    )
    return response.status_code == 201


def main(page: ft.Page) -> None:
    page.title = "Modular Chat Client"
    page.window_maximized = True
    show_login_register_ui(page, "login")


ft.app(target=main)
