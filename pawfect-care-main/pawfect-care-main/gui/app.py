import customtkinter as ctk

from gui.login.login_view import LoginView
from gui.admin.dashboard import AdminDashboard
from utils.theme import COLORS


class PawfectCareApp(ctk.CTk):
    """Main Pawfect Care application."""

    def __init__(self):
        super().__init__()

        self.title("Pawfect Care")
        self.geometry("1000x650")

        self.configure(
            fg_color=COLORS["background"]
        )

        self.current_user = None

        self.show_login()

    def clear_window(self):
        """Remove all widgets from the window."""

        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self):
        """Display the login screen."""

        self.current_user = None

        self.clear_window()

        login_view = LoginView(
            self,
            self.login_success
        )

        login_view.pack(
            fill="both",
            expand=True
        )

    def login_success(self, user):
        """Handle a successful login."""

        self.current_user = user

        if user["role"] == "Admin":
            self.show_admin_dashboard()

        elif user["role"] == "Groomer":
            self.show_groomer_dashboard()

    def show_admin_dashboard(self):
        """Display the Admin dashboard."""

        self.clear_window()

        dashboard = AdminDashboard(
            self,
            self.current_user,
            self.show_login
        )

        dashboard.pack(
            fill="both",
            expand=True
        )

    def show_groomer_dashboard(self):
        """Display the Groomer dashboard."""

        # Temporary until we build the Groomer dashboard.
        self.clear_window()

        label = ctk.CTkLabel(
            self,
            text="Groomer Dashboard - Coming Soon",
            font=("Arial", 28, "bold")
        )

        label.pack(
            expand=True
        )