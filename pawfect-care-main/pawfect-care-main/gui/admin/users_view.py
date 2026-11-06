import sqlite3

import customtkinter as ctk

from services.user_service import (
    USER_ROLES,
    UserRuleError,
    add_user,
    get_all_users,
    reset_user_password,
    set_user_active,
    update_user,
)
from utils.theme import COLORS
from utils.decor import paw_banner


class UsersView(ctk.CTkFrame):
    """Admin interface for user accounts, roles, and password resets."""

    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color=COLORS["background"])
        self.current_user = current_user
        self.create_widgets()
        self.load_users()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 18))
        title_group = ctk.CTkFrame(header, fg_color="transparent")
        title_group.pack(side="left")
        ctk.CTkLabel(title_group, text="User Management", font=("Arial", 29, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_group, text="Manage accounts, roles, and access",
                     font=("Arial", 14), text_color=COLORS["muted_text"]).pack(anchor="w")
        ctk.CTkButton(header, text="+ Add User", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"],
                      command=self.show_add_form).pack(side="right", pady=8)

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=30, pady=(0, 12))
        self.search_entry = ctk.CTkEntry(
            filters, placeholder_text="Search username or full name",
            fg_color=COLORS["input"], border_color=COLORS["blue"], text_color=COLORS["text"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _event: self.load_users())
        self.role_filter = ctk.CTkOptionMenu(
            filters, values=["All roles", *USER_ROLES], fg_color=COLORS["blue"],
            button_color=COLORS["blue_hover"], command=lambda _value: self.load_users()
        )
        self.role_filter.pack(side="right", padx=(6, 0))
        self.active_filter = ctk.CTkOptionMenu(
            filters, values=["All accounts", "Active", "Inactive"], fg_color=COLORS["blue"],
            button_color=COLORS["blue_hover"], command=lambda _value: self.load_users()
        )
        self.active_filter.pack(side="right")
        self.role_filter.set("All roles")
        self.active_filter.set("All accounts")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 25))

    def load_users(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        users = get_all_users()
        query = self.search_entry.get().strip().casefold()
        role_filter = self.role_filter.get()
        active_filter = self.active_filter.get()
        users = [user for user in users
                 if (not query or query in f"{user[1]} {user[2]}".casefold())
                 and (role_filter == "All roles" or user[3] == role_filter)
                 and (active_filter == "All accounts"
                      or (active_filter == "Active" and user[4])
                      or (active_filter == "Inactive" and not user[4]))]
        if not users:
            ctk.CTkLabel(self.list_frame, text="No users match these filters.",
                         font=("Arial", 16), text_color=COLORS["muted_text"]).pack(pady=45)
            return

        for user in users:
            user_id, username, full_name, role, is_active, created_at = user
            card = ctk.CTkFrame(self.list_frame, fg_color=COLORS["card"], corner_radius=12)
            card.pack(fill="x", pady=5)
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=15, pady=11)
            ctk.CTkLabel(info, text=f"{full_name}  (@{username})",
                         font=("Arial", 15, "bold"), text_color=COLORS["text"],
                         anchor="w").pack(fill="x")
            status = "Active" if is_active else "Inactive"
            ctk.CTkLabel(info, text=f"{role}  |  {status}  |  Created {created_at}",
                         font=("Arial", 12), text_color=COLORS["muted_text"],
                         anchor="w").pack(fill="x", pady=(2, 0))
            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(side="right", padx=10, pady=8)
            ctk.CTkButton(actions, text="Edit", width=62, fg_color=COLORS["yellow"],
                          hover_color=COLORS["yellow_hover"], text_color=COLORS["text"],
                          command=lambda record=user: self.show_edit_form(record)).pack(side="left", padx=3)
            ctk.CTkButton(actions, text="Reset Password", width=115, fg_color=COLORS["blue"],
                          hover_color=COLORS["blue_hover"],
                          command=lambda record=user: self.show_reset_form(record)).pack(side="left", padx=3)
            if user_id == self.current_user["user_id"]:
                ctk.CTkButton(actions, text="Signed in", width=95, state="disabled",
                              fg_color=COLORS["muted_text"], text_color=COLORS["text"]
                              ).pack(side="left", padx=3)
            else:
                ctk.CTkButton(
                    actions, text="Deactivate" if is_active else "Activate", width=95,
                    fg_color=COLORS["pink"] if is_active else COLORS["success"],
                    hover_color=COLORS["pink_hover"] if is_active else COLORS["success"],
                    text_color=COLORS["text"],
                    command=lambda uid=user_id, active=bool(is_active), name=username:
                        self.confirm_active_change(uid, name, not active)
                ).pack(side="left", padx=3)

    def show_add_form(self):
        self.show_user_form()

    def show_edit_form(self, user):
        self.show_user_form(user)

    def show_user_form(self, user=None):
        editing = user is not None
        window = ctk.CTkToplevel(self)
        window.title("Edit User" if editing else "Add User")
        window.geometry("500x570" if editing else "500x650")
        window.minsize(460, 500)
        window.transient(self.winfo_toplevel())
        window.grab_set()
        window.configure(fg_color=COLORS["background"])
        paw_banner(window, "Edit User" if editing else "Add User",
                   "Manage who can use Pawfect Care")
        form = ctk.CTkScrollableFrame(window, fg_color=COLORS["card"], corner_radius=14,
                                      border_width=2, border_color=COLORS["yellow"])
        form.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        name_entry = self.create_entry(form, "Full Name", "Enter full name")
        username_entry = self.create_entry(form, "Username", "At least 3 characters, no spaces")
        ctk.CTkLabel(form, text="Role", text_color=COLORS["text"]).pack(
            anchor="w", padx=24, pady=(13, 4))
        role_menu = ctk.CTkOptionMenu(form, values=list(USER_ROLES), fg_color=COLORS["blue"],
                                      button_color=COLORS["blue_hover"])
        role_menu.pack(fill="x", padx=24)
        password_entry = None
        confirm_password_entry = None
        if not editing:
            password_entry = self.create_entry(form, "Initial Password", "At least 12 characters", show="*")
            confirm_password_entry = self.create_entry(form, "Confirm Password", "Re-enter password", show="*")
            role_menu.set("Groomer")
        else:
            role_menu.set(user[3])
            name_entry.insert(0, user[2])
            username_entry.insert(0, user[1])
        error_label = ctk.CTkLabel(form, text="", text_color=COLORS["error"], wraplength=400)
        error_label.pack(pady=(12, 5))
        ctk.CTkButton(
            form, text="Update User" if editing else "Create User",
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            command=lambda: self.save_user(
                window, user[0] if editing else None, name_entry, username_entry,
                role_menu, password_entry, confirm_password_entry, error_label
            )
        ).pack(pady=(5, 18))

    def create_entry(self, parent, label, placeholder, show=None):
        ctk.CTkLabel(parent, text=label, text_color=COLORS["text"]).pack(
            anchor="w", padx=24, pady=(13, 4))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, show=show,
                             fg_color=COLORS["input"], border_color=COLORS["blue"],
                             text_color=COLORS["text"])
        entry.pack(fill="x", padx=24)
        return entry

    def save_user(self, window, user_id, name_entry, username_entry, role_menu,
                  password_entry, confirm_password_entry, error_label):
        if user_id is None and password_entry.get() != confirm_password_entry.get():
            error_label.configure(text="Passwords do not match.")
            return
        try:
            if user_id is None:
                add_user(username_entry.get(), name_entry.get(), role_menu.get(),
                         password_entry.get())
            else:
                update_user(user_id, username_entry.get(), name_entry.get(), role_menu.get(),
                            acting_user_id=self.current_user["user_id"])
        except (UserRuleError, sqlite3.IntegrityError) as error:
            error_label.configure(text=str(error))
            return
        window.destroy()
        self.load_users()
        self.show_message("User updated successfully." if user_id is not None else
                          "User created successfully.")

    def show_reset_form(self, user):
        user_id, username = user[0], user[1]
        window = ctk.CTkToplevel(self)
        window.title("Reset Password")
        window.geometry("460x380")
        window.resizable(False, False)
        window.transient(self.winfo_toplevel())
        window.grab_set()
        window.configure(fg_color=COLORS["background"])
        ctk.CTkLabel(window, text=f"Reset password for {username}",
                     font=("Arial", 20, "bold"), text_color=COLORS["blue"]).pack(pady=(24, 12))
        form = ctk.CTkFrame(window, fg_color=COLORS["card"], corner_radius=14)
        form.pack(fill="both", expand=True, padx=24, pady=(0, 22))
        password = self.create_entry(form, "New Password", "At least 12 characters", show="*")
        confirm = self.create_entry(form, "Confirm Password", "Re-enter new password", show="*")
        error_label = ctk.CTkLabel(form, text="", text_color=COLORS["error"])
        error_label.pack(pady=(12, 4))
        ctk.CTkButton(form, text="Reset Password", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"],
                      command=lambda: self.save_reset(window, user_id, password.get(),
                                                      confirm.get(), error_label)).pack(pady=(4, 18))

    def save_reset(self, window, user_id, password, confirmation, error_label):
        if password != confirmation:
            error_label.configure(text="Passwords do not match.")
            return
        try:
            reset_user_password(user_id, password)
        except UserRuleError as error:
            error_label.configure(text=str(error))
            return
        window.destroy()
        self.show_message("Password reset successfully.")

    def confirm_active_change(self, user_id, username, make_active):
        action = "activate" if make_active else "deactivate"
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"{action.title()} User")
        dialog.geometry("420x220")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        ctk.CTkLabel(dialog, text=f"Are you sure you want to {action} {username}?",
                     font=("Arial", 14), text_color=COLORS["text"],
                     wraplength=360).pack(pady=(30, 15))
        error_label = ctk.CTkLabel(dialog, text="", text_color=COLORS["error"], wraplength=370)
        error_label.pack(pady=4)
        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(pady=10)
        ctk.CTkButton(buttons, text="Cancel", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"], command=dialog.destroy).pack(side="left", padx=5)
        ctk.CTkButton(buttons, text=action.title(), fg_color=COLORS["pink"],
                      hover_color=COLORS["pink_hover"], text_color=COLORS["text"],
                      command=lambda: self.save_active_change(user_id, make_active, dialog,
                                                              error_label)).pack(side="left", padx=5)

    def save_active_change(self, user_id, make_active, dialog, error_label):
        try:
            set_user_active(user_id, make_active,
                            acting_user_id=self.current_user["user_id"])
        except UserRuleError as error:
            error_label.configure(text=str(error))
            return
        dialog.destroy()
        self.load_users()
        self.show_message("User activated." if make_active else "User deactivated.")

    def show_message(self, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title("User Management")
        dialog.geometry("400x180")
        dialog.transient(self.winfo_toplevel())
        dialog.configure(fg_color=COLORS["background"])
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=message, text_color=COLORS["text"],
                     wraplength=350).pack(pady=28)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy,
                      fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"]).pack()
