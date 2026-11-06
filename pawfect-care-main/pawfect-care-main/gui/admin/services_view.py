import sqlite3
import math

import customtkinter as ctk

from services.service_service import (
    add_service,
    delete_service,
    get_all_categories,
    get_all_services,
    update_service,
)
from utils.theme import COLORS


class ServicesView(ctk.CTkFrame):
    """Admin page for managing grooming services."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["background"])
        self.create_widgets()
        self.load_services()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="Services", font=("Arial", 30, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Manage grooming services, prices, and durations",
                     font=("Arial", 14), text_color=COLORS["muted_text"]).pack(anchor="w")
        ctk.CTkButton(header, text="+ Add Service", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"],
                      command=self.show_add_service_form).pack(side="right", pady=10)

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=30, pady=(0, 12))
        self.search_entry = ctk.CTkEntry(
            filters, placeholder_text="Search service name or description",
            fg_color=COLORS["input"], border_color=COLORS["blue"], text_color=COLORS["text"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _event: self.load_services())
        self.category_filter = ctk.CTkOptionMenu(
            filters, values=["All categories"], fg_color=COLORS["blue"],
            button_color=COLORS["blue_hover"], command=lambda _value: self.load_services()
        )
        self.category_filter.pack(side="right", padx=(6, 0))
        self.status_filter = ctk.CTkOptionMenu(
            filters, values=["All status", "Active only", "Inactive only"],
            fg_color=COLORS["blue"], button_color=COLORS["blue_hover"],
            command=lambda _value: self.load_services()
        )
        self.status_filter.pack(side="right", padx=(6, 0))
        self.category_filter.set("All categories")
        self.status_filter.set("All status")

        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=COLORS["card"], corner_radius=15
        )
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def load_services(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        services = get_all_services()
        category_values = ["All categories"] + [name for _, name in get_all_categories()]
        if self.category_filter.get() not in category_values:
            self.category_filter.set("All categories")
        self.category_filter.configure(values=category_values)
        query = self.search_entry.get().strip().casefold()
        selected_category = self.category_filter.get()
        selected_status = self.status_filter.get()
        services = [service for service in services
                    if (selected_category == "All categories" or service[2] == selected_category)
                    and (selected_status == "All status"
                         or (selected_status == "Active only" and service[7])
                         or (selected_status == "Inactive only" and not service[7]))
                    and (not query or query in " ".join(
                        str(value or "") for value in (service[3], service[4], service[2])
                    ).casefold())]
        headers = ("ID", "Service", "Category", "Price", "Duration", "Status", "Actions")
        for column, text in enumerate(headers):
            self.list_frame.grid_columnconfigure(column, weight=1 if column != 6 else 2)
            ctk.CTkLabel(self.list_frame, text=text, font=("Arial", 12, "bold"),
                         fg_color=COLORS["yellow"], text_color=COLORS["text"],
                         corner_radius=8).grid(row=0, column=column, sticky="ew",
                                               padx=2, pady=(10, 10))

        if not services:
            empty = ctk.CTkLabel(self.list_frame,
                                 text="No services found. Add a service to get started.",
                                 font=("Arial", 16), text_color=COLORS["muted_text"])
            empty.grid(row=1, column=0, columnspan=len(headers), pady=50)
            return

        for row, service in enumerate(services, start=1):
            service_id, category_id, category, name, description, price, duration, active = service
            values = (service_id, name, category, f"₱{price:,.2f}", f"{duration} min",
                      "Active" if active else "Inactive")
            for column, value in enumerate(values):
                ctk.CTkLabel(self.list_frame, text=str(value),
                             text_color=COLORS["text"]).grid(
                    row=row, column=column, sticky="ew", padx=5, pady=10
                )
            actions = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            actions.grid(row=row, column=6, padx=5, pady=5)
            ctk.CTkButton(actions, text="Edit", width=65, fg_color=COLORS["yellow"],
                          hover_color=COLORS["yellow_hover"], text_color=COLORS["text"],
                          command=lambda record=service: self.show_service_form(record)).pack(
                              side="left", padx=(0, 5))
            ctk.CTkButton(actions, text="Delete", width=65, fg_color=COLORS["pink"],
                          hover_color=COLORS["pink_hover"], text_color=COLORS["text"],
                          command=lambda record_id=service_id: self.confirm_delete(record_id)).pack(
                              side="left")

    def show_add_service_form(self):
        self.show_service_form()

    def show_service_form(self, service=None):
        categories = get_all_categories()
        if not categories:
            self.show_message("No service categories are available. Seed the database first.")
            return

        window = ctk.CTkToplevel(self)
        is_edit = service is not None
        window.title("Edit Service" if is_edit else "Add Service")
        window.geometry("520x650")
        window.minsize(480, 540)
        window.transient(self.winfo_toplevel())
        window.grab_set()
        window.configure(fg_color=COLORS["background"])
        ctk.CTkLabel(window, text="Edit Service" if is_edit else "Add Service",
                     font=("Arial", 26, "bold"), text_color=COLORS["blue"]).pack(pady=(20, 12))
        form = ctk.CTkScrollableFrame(window, fg_color=COLORS["card"], corner_radius=15)
        form.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        category_options = {name: category_id for category_id, name in categories}
        ctk.CTkLabel(form, text="Category", text_color=COLORS["text"]).pack(
            anchor="w", padx=25, pady=(15, 3))
        category_menu = ctk.CTkOptionMenu(
            form, values=list(category_options), fg_color=COLORS["blue"],
            button_color=COLORS["blue_hover"]
        )
        category_menu.pack(fill="x", padx=25)

        fields = {}
        for label, key, placeholder in (
            ("Service Name", "service_name", "Required"),
            ("Description", "description", "Optional"),
            ("Price (₱)", "price", "e.g. 250.00"),
            ("Duration (minutes)", "duration", "e.g. 30"),
        ):
            ctk.CTkLabel(form, text=label, text_color=COLORS["text"]).pack(
                anchor="w", padx=25, pady=(12, 3))
            entry = ctk.CTkEntry(form, placeholder_text=placeholder,
                                 fg_color=COLORS["input"], border_color=COLORS["blue"],
                                 text_color=COLORS["text"])
            entry.pack(fill="x", padx=25)
            fields[key] = entry

        active_check = ctk.CTkCheckBox(form, text="Available for booking",
                                       text_color=COLORS["text"],
                                       fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"])
        active_check.pack(anchor="w", padx=25, pady=(15, 5))
        error_label = ctk.CTkLabel(form, text="", text_color=COLORS["error"], wraplength=400)
        error_label.pack(pady=(10, 4))

        if is_edit:
            service_id, current_category, category, name, description, price, duration, active = service
            category_name = next((name for name, cid in category_options.items()
                                  if cid == current_category), list(category_options)[0])
            category_menu.set(category_name)
            for key, value in {"service_name": name, "description": description or "",
                               "price": str(price), "duration": str(duration)}.items():
                fields[key].insert(0, value)
            if active:
                active_check.select()
        else:
            service_id = None
            category_menu.set(list(category_options)[0])
            active_check.select()

        ctk.CTkButton(
            form, text="Update Service" if is_edit else "Save Service",
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            command=lambda: self.save_service(window, service_id, category_menu,
                                              category_options, fields, active_check,
                                              error_label)
        ).pack(pady=(8, 20))

    def save_service(self, window, service_id, category_menu, category_options,
                     fields, active_check, error_label):
        name = fields["service_name"].get().strip()
        if not name:
            error_label.configure(text="Service name is required.")
            return
        try:
            price = float(fields["price"].get().strip())
            duration = int(fields["duration"].get().strip())
            if not math.isfinite(price) or price < 0 or duration <= 0:
                raise ValueError
        except ValueError:
            error_label.configure(text="Enter a price of zero or more and a whole duration above zero.")
            return

        try:
            category_id = category_options[category_menu.get()]
            if service_id is None:
                add_service(category_id, name, fields["description"].get(), price, duration)
            else:
                update_service(service_id, category_id, name, fields["description"].get(),
                               price, duration, active_check.get())
        except sqlite3.IntegrityError:
            error_label.configure(text="A service with that name already exists in this category.")
            return
        window.destroy()
        self.load_services()
        self.show_message("Service updated successfully." if service_id is not None else
                          "Service added successfully.")

    def confirm_delete(self, service_id):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Delete Service")
        dialog.geometry("430x230")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        ctk.CTkLabel(dialog, text="Delete this service?\nServices on appointments cannot be deleted.",
                     font=("Arial", 14), text_color=COLORS["text"]).pack(pady=(30, 15))
        error_label = ctk.CTkLabel(dialog, text="", text_color=COLORS["error"], wraplength=380)
        error_label.pack(pady=5)
        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(pady=10)
        ctk.CTkButton(buttons, text="Cancel", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"], command=dialog.destroy).pack(side="left", padx=5)
        ctk.CTkButton(buttons, text="Delete", fg_color=COLORS["pink"],
                      hover_color=COLORS["pink_hover"], text_color=COLORS["text"],
                      command=lambda: self.delete_service_record(service_id, dialog, error_label)).pack(side="left", padx=5)

    def delete_service_record(self, service_id, dialog, error_label):
        try:
            delete_service(service_id)
        except sqlite3.IntegrityError:
            error_label.configure(text="This service is used by an appointment and cannot be deleted.")
            return
        dialog.destroy()
        self.load_services()
        self.show_message("Service deleted successfully.")

    def show_message(self, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Services")
        dialog.geometry("390x170")
        dialog.transient(self.winfo_toplevel())
        dialog.configure(fg_color=COLORS["background"])
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=message, text_color=COLORS["text"],
                     wraplength=340).pack(pady=30)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy,
                      fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"]).pack()
