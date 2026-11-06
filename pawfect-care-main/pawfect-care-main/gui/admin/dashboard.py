import customtkinter as ctk
from datetime import date, datetime

from utils.theme import COLORS
from services.dashboard_service import APPOINTMENT_STATUSES, get_dashboard_data
from gui.customers.customers_view import CustomersView
from gui.admin.pets_view import PetsView
from gui.admin.services_view import ServicesView
from gui.admin.appointments_view import AppointmentsView
from gui.admin.payments_view import PaymentsView
from gui.admin.users_view import UsersView


class AdminDashboard(ctk.CTkFrame):
    """Admin dashboard for Pawfect Care."""

    def __init__(self, parent, user, on_logout):
        super().__init__(
            parent,
            fg_color=COLORS["background"]
        )

        self.user = user
        self.on_logout = on_logout
        self.active_button = None

        self.create_layout()

    def create_layout(self):
        """Create the Admin dashboard layout."""

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0,
            fg_color=COLORS["sidebar"]
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        # Main content area
        self.content = ctk.CTkFrame(
            self,
            fg_color=COLORS["background"],
            corner_radius=0
        )

        self.content.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.create_sidebar()
        self.show_dashboard()

    def create_sidebar(self):
        """Create the sidebar navigation."""

        # Logo / system name
        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Pawfect Care",
            font=("Arial", 22, "bold"),
            text_color=COLORS["sidebar_text"]
        )

        logo_label.pack(
            pady=(30, 40),
            padx=20
        )

        # Navigation buttons
        self.create_nav_button(
            "Dashboard",
            self.show_dashboard
        )

        self.create_nav_button(
            "Customers",
            self.show_customers
        )

        self.create_nav_button(
            "Pets",
            self.show_pets
        )

        self.create_nav_button(
            "Services",
            self.show_services
        )

        self.create_nav_button(
            "Appointments",
            self.show_appointments
        )

        self.create_nav_button(
            "Payments",
            self.show_payments
        )

        self.create_nav_button(
            "Users",
            self.show_users
        )

        # Spacer pushes Logout toward the bottom
        spacer = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        spacer.pack(
            fill="both",
            expand=True
        )

        # Logout button
        logout_button = ctk.CTkButton(
            self.sidebar,
            text="Logout",
            fg_color=COLORS["pink"],
            hover_color=COLORS["pink_hover"],
            text_color=COLORS["text"],
            command=self.on_logout
        )

        logout_button.pack(
            fill="x",
            padx=15,
            pady=20
        )

    def create_nav_button(self, text, command):
        """Create a sidebar navigation button."""

        button = ctk.CTkButton(
            self.sidebar,
            text=text,
            anchor="w",
            height=45,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["sidebar_hover"],
            text_color=COLORS["sidebar_text"],
            command=command
        )

        button.pack(
            fill="x",
            padx=15,
            pady=5
        )

    def clear_content(self):
        """Remove the current page content."""

        for widget in self.content.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        """Display the live dashboard page."""
        self.clear_content()
        self.render_dashboard_page()

    def render_dashboard_page(self):
        """Build dashboard cards and today's appointment list from live data."""
        data = get_dashboard_data()
        page = ctk.CTkScrollableFrame(self.content, fg_color=COLORS["background"])
        page.pack(fill="both", expand=True)

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(28, 18))
        title_group = ctk.CTkFrame(header, fg_color="transparent")
        title_group.pack(side="left")
        ctk.CTkLabel(title_group, text="Dashboard", font=("Arial", 30, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_group, text=f"Welcome back, {self.user['full_name']}!",
                     font=("Arial", 15), text_color=COLORS["muted_text"]).pack(anchor="w")
        ctk.CTkLabel(header, text=date.today().strftime("%A, %B %d, %Y"),
                     font=("Arial", 13), text_color=COLORS["muted_text"]).pack(side="right", pady=8)

        summary = ctk.CTkFrame(page, fg_color="transparent")
        summary.pack(fill="x", padx=24, pady=(0, 20))
        for column in range(4):
            summary.grid_columnconfigure(column, weight=1)
        metrics = (
            ("Customers", data["customer_count"], COLORS["blue"]),
            ("Pets", data["pet_count"], COLORS["pink"]),
            ("Appointments", data["appointment_count"], COLORS["yellow"]),
            ("Today", len(data["today_appointments"]), COLORS["blue"]),
        )
        for column, (label, value, accent) in enumerate(metrics):
            card = ctk.CTkFrame(summary, fg_color=COLORS["card"], corner_radius=13,
                                border_width=2, border_color=accent)
            card.grid(row=0, column=column, sticky="ew", padx=6, pady=4)
            ctk.CTkLabel(card, text=label, font=("Arial", 13),
                         text_color=COLORS["muted_text"]).pack(anchor="w", padx=15, pady=(13, 2))
            ctk.CTkLabel(card, text=str(value), font=("Arial", 27, "bold"),
                         text_color=COLORS["text"]).pack(anchor="w", padx=15, pady=(0, 12))

        ctk.CTkLabel(page, text="Appointment Statistics", font=("Arial", 20, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w", padx=30, pady=(0, 8))
        statistics = ctk.CTkFrame(page, fg_color="transparent")
        statistics.pack(fill="x", padx=24, pady=(0, 20))
        for column in range(5):
            statistics.grid_columnconfigure(column, weight=1)
        status_colors = {
            "Pending": COLORS["yellow"], "Confirmed": COLORS["blue"],
            "In Progress": COLORS["pink"], "Completed": COLORS["success"],
            "Cancelled": COLORS["muted_text"],
        }
        for column, status in enumerate(APPOINTMENT_STATUSES):
            card = ctk.CTkFrame(statistics, fg_color=COLORS["card"], corner_radius=10)
            card.grid(row=0, column=column, sticky="ew", padx=5, pady=3)
            ctk.CTkLabel(card, text=status, font=("Arial", 11),
                         text_color=COLORS["muted_text"]).pack(pady=(10, 1))
            ctk.CTkLabel(card, text=str(data["status_counts"][status]),
                         font=("Arial", 21, "bold"), text_color=status_colors[status]).pack(pady=(0, 9))

        today_header = ctk.CTkFrame(page, fg_color="transparent")
        today_header.pack(fill="x", padx=30, pady=(0, 8))
        ctk.CTkLabel(today_header, text="Today's Appointments", font=("Arial", 20, "bold"),
                     text_color=COLORS["text"]).pack(side="left")
        ctk.CTkLabel(today_header, text=str(len(data["today_appointments"])),
                     font=("Arial", 13, "bold"), text_color=COLORS["blue"]).pack(side="right")
        today_list = ctk.CTkFrame(page, fg_color=COLORS["card"], corner_radius=13)
        today_list.pack(fill="x", padx=30, pady=(0, 25))
        if not data["today_appointments"]:
            ctk.CTkLabel(today_list, text="No appointments scheduled for today.",
                         font=("Arial", 14), text_color=COLORS["muted_text"]).pack(pady=25)
        else:
            for row, appointment in enumerate(data["today_appointments"]):
                (_, number, time_text, status, pet_name,
                 customer_name, service_names) = appointment
                if row:
                    ctk.CTkFrame(today_list, height=1, fg_color=COLORS["input_border"]).pack(
                        fill="x", padx=15, pady=0)
                item = ctk.CTkFrame(today_list, fg_color="transparent")
                item.pack(fill="x", padx=15, pady=10)
                try:
                    display_time = datetime.strptime(time_text, "%H:%M").strftime("%I:%M %p")
                except ValueError:
                    display_time = time_text
                ctk.CTkLabel(item, text=display_time, width=82,
                             font=("Arial", 14, "bold"), text_color=COLORS["blue"]).pack(side="left", anchor="n")
                info = ctk.CTkFrame(item, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=(10, 8))
                ctk.CTkLabel(info, text=f"{pet_name} | {customer_name} | {number}",
                             font=("Arial", 13, "bold"), text_color=COLORS["text"],
                             anchor="w").pack(fill="x")
                if service_names:
                    ctk.CTkLabel(info, text=service_names, font=("Arial", 11),
                                 text_color=COLORS["muted_text"], anchor="w",
                                 wraplength=620).pack(fill="x")
                ctk.CTkLabel(item, text=status, font=("Arial", 11, "bold"),
                             text_color=COLORS["blue"] if status != "Cancelled" else COLORS["error"]).pack(side="right")

    def show_customers(self):
        """Display the Customers management page."""

        self.clear_content()

        customers_view = CustomersView(
            self.content
        )

        customers_view.pack(
            fill="both",
            expand=True
        )

    def show_pets(self):
        """Display the Pets page."""

        self.clear_content()

        pets_view = PetsView(self.content)
        pets_view.pack(fill="both", expand=True)

    def show_services(self):
        """Display the Services page."""

        self.clear_content()

        services_view = ServicesView(self.content)
        services_view.pack(fill="both", expand=True)

    def show_appointments(self):
        """Display the Appointments page."""

        self.clear_content()

        appointments_view = AppointmentsView(self.content)
        appointments_view.pack(fill="both", expand=True)

    def show_payments(self):
        """Display the Payments page."""

        self.clear_content()

        payments_view = PaymentsView(self.content)
        payments_view.pack(fill="both", expand=True)

    def show_users(self):
        """Display the Users page."""

        self.clear_content()

        users_view = UsersView(self.content, self.user)
        users_view.pack(fill="both", expand=True)

    def show_placeholder(self, page_name):
        """Display a temporary page."""

        self.clear_content()

        title = ctk.CTkLabel(
            self.content,
            text=page_name,
            font=("Arial", 30, "bold"),
            text_color=COLORS["text"]
        )

        title.pack(
            pady=50
        )

        message = ctk.CTkLabel(
            self.content,
            text=f"{page_name} management is coming next.",
            font=("Arial", 16),
            text_color=COLORS["muted_text"]
        )

        message.pack()

