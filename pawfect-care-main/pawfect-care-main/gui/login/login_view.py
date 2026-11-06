import customtkinter as ctk

from services.auth_service import AccountDeactivatedError, authenticate_user
from utils.validators import validate_login_input
from utils.theme import COLORS
from utils.decor import paw_strip, scatter_paws


class LoginView(ctk.CTkFrame):
    """Login screen for Pawfect Care."""

    def __init__(self, parent, on_login_success):
        super().__init__(
            parent,
            fg_color=COLORS["background"]
        )

        self.on_login_success = on_login_success

        self.create_widgets()

    def create_widgets(self):
        """Create the login interface."""

        # Soft paw prints in the background (added first so the card sits on top)
        scatter_paws(self)

        # Center container
        login_frame = ctk.CTkFrame(
            self,
            width=400,
            height=400,
            fg_color=COLORS["card"],
            corner_radius=24,
            border_width=3,
            border_color=COLORS["pink"]
        )

        login_frame.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        # Title
        title_label = ctk.CTkLabel(
            login_frame,
            text="🐾 Pawfect Care",
            font=("Arial", 28, "bold"),
            text_color=COLORS["blue"]
        )

        title_label.pack(
            pady=(40, 10)
        )

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            login_frame,
            text="Pet Grooming Management System",
            font=("Arial", 14),
            text_color=COLORS["pink"]
        )

        subtitle_label.pack(
            pady=(0, 8)
        )

        paw_strip(login_frame, pady=(0, 18))

        # Username
        username_label = ctk.CTkLabel(
            login_frame,
            text="Username",
            text_color=COLORS["text"]
        )

        username_label.pack(
            padx=40,
            anchor="w"
        )

        self.username_entry = ctk.CTkEntry(
            login_frame,
            width=320,
            placeholder_text="Enter your username",
            fg_color=COLORS["input"],
            border_color=COLORS["blue"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted_text"]
        )

        self.username_entry.pack(
            padx=40,
            pady=(5, 15)
        )

        # Password
        password_label = ctk.CTkLabel(
            login_frame,
            text="Password",
            text_color=COLORS["text"]
        )

        password_label.pack(
            padx=40,
            anchor="w"
        )

        self.password_entry = ctk.CTkEntry(
            login_frame,
            width=320,
            placeholder_text="Enter your password",
            show="*",
            fg_color=COLORS["input"],
            border_color=COLORS["blue"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted_text"]
        )

        self.password_entry.pack(
            padx=40,
            pady=(5, 15)
        )

        # Error / status message
        self.message_label = ctk.CTkLabel(
            login_frame,
            text="",
            font=("Arial", 12),
            text_color=COLORS["error"]
        )

        self.message_label.pack(
            pady=(0, 10)
        )

        # Login button
        login_button = ctk.CTkButton(
            login_frame,
            text="Login",
            width=320,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            command=self.handle_login
        )

        login_button.pack(
            padx=40,
            pady=(0, 30)
        )

    def handle_login(self):
        """Handle the login button click."""

        username = self.username_entry.get()
        password = self.password_entry.get()

        # Validate input
        is_valid, message = validate_login_input(
            username,
            password
        )

        if not is_valid:
            self.message_label.configure(
                text=message
            )
            return

        # Authenticate user
        try:
            user = authenticate_user(username.strip(), password)
        except AccountDeactivatedError as error:
            self.message_label.configure(text=str(error))
            return

        if user is None:
            self.message_label.configure(
                text="Invalid username or password."
            )
            return

        # Clear message
        self.message_label.configure(
            text=""
        )

        # Send authenticated user to the main app
        self.on_login_success(user)

