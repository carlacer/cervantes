import re
import sqlite3

import customtkinter as ctk

from utils.theme import COLORS
from utils.decor import paw_banner
from services.customer_service import (
    CustomerRuleError,
    add_customer,
    delete_customer,
    get_all_customers,
    update_customer
)


class CustomersView(ctk.CTkFrame):
    """Customers management page."""

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=COLORS["background"]
        )

        self.create_widgets()
        self.load_customers()

    def create_widgets(self):
        """Create the Customers page widgets."""

        # Header
        header = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=30,
            pady=(30, 20)
        )

        # Page title section
        title_frame = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )

        title_frame.pack(
            side="left"
        )

        title_label = ctk.CTkLabel(
            title_frame,
            text="Customers",
            font=("Arial", 30, "bold"),
            text_color=COLORS["text"]
        )

        title_label.pack(
            anchor="w"
        )

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Manage your pet grooming customers",
            font=("Arial", 14),
            text_color=COLORS["muted_text"]
        )

        subtitle_label.pack(
            anchor="w"
        )

        # Add Customer button
        add_button = ctk.CTkButton(
            header,
            text="+ Add Customer",
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            command=self.show_add_customer_form
        )

        add_button.pack(
            side="right",
            pady=10
        )

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=30, pady=(0, 12))
        self.search_entry = ctk.CTkEntry(
            filters, placeholder_text="Search name, contact, email, or address",
            fg_color=COLORS["input"], border_color=COLORS["blue"], text_color=COLORS["text"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _event: self.load_customers())
        self.email_filter = ctk.CTkOptionMenu(
            filters, values=["All customers", "With email", "Without email"],
            fg_color=COLORS["blue"], button_color=COLORS["blue_hover"],
            command=lambda _value: self.load_customers()
        )
        self.email_filter.pack(side="right")
        self.email_filter.set("All customers")

        # Customer list container
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=15
        )

        self.list_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 30)
        )

    def load_customers(self):
        """Load customers from the database."""

        # Remove existing customer rows
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        customers = get_all_customers()
        query = self.search_entry.get().strip().casefold()
        email_filter = self.email_filter.get()
        customers = [customer for customer in customers
                     if (not query or query in " ".join(
                         str(value or "") for value in customer[:6]
                     ).casefold())
                     and (email_filter == "All customers"
                          or (email_filter == "With email" and bool(customer[4]))
                          or (email_filter == "Without email" and not customer[4]))]

        # Configure table column widths
        self.list_frame.grid_columnconfigure(0, weight=1)  # ID
        self.list_frame.grid_columnconfigure(1, weight=2)  # Name
        self.list_frame.grid_columnconfigure(2, weight=2)  # Contact Number
        self.list_frame.grid_columnconfigure(3, weight=2)  # Email
        self.list_frame.grid_columnconfigure(4, weight=2)  # Address
        self.list_frame.grid_columnconfigure(5, weight=2)  # Actions

        # Table header
        headers = [
            "ID",
            "Name",
            "Contact Number",
            "Email",
            "Address",
            "Actions"
        ]

        for column, header in enumerate(headers):
            header_label = ctk.CTkLabel(
                self.list_frame,
                text=header,
                font=("Arial", 12, "bold"),
                fg_color=COLORS["yellow"],
                text_color=COLORS["text"],
                corner_radius=8
            )

            header_label.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=2,
                pady=(10, 10)
            )


        # No customers message
        if not customers:
            empty_label = ctk.CTkLabel(
                self.list_frame,
                text="No customers found. Add your first customer! 🐾",
                font=("Arial", 16),
                text_color=COLORS["muted_text"]
            )

            empty_label.grid(
                row=1,
                column=0,
                columnspan=6,
                pady=50
            )

            return


        # Customer rows
        for row_index, customer in enumerate(customers, start=1):

            customer_id, first_name, last_name, contact, email, address, _ = customer

            values = [
                customer_id,
                f"{first_name} {last_name}",
                contact,
                email or "-",
                address or "-"
            ]

            # Display customer information
            for column, value in enumerate(values):

                label = ctk.CTkLabel(
                    self.list_frame,
                    text=str(value),
                    text_color=COLORS["text"]
                )

                label.grid(
                    row=row_index,
                    column=column,
                    sticky="ew",
                    padx=5,
                    pady=10
                )

            # Actions frame
            actions_frame = ctk.CTkFrame(
                self.list_frame,
                fg_color="transparent"
            )

            actions_frame.grid(
                row=row_index,
                column=5,
                padx=5,
                pady=5
            )

            # Edit button
            edit_button = ctk.CTkButton(
                actions_frame,
                text="Edit",
                width=70,
                fg_color=COLORS["yellow"],
                hover_color=COLORS["yellow_hover"],
                text_color=COLORS["text"],
                command=lambda customer=customer: self.show_edit_customer_form(
                    customer
                )
            )

            edit_button.pack(
                side="left",
                padx=(0, 5)
            )

            # Delete button
            delete_button = ctk.CTkButton(
                actions_frame,
                text="Delete",
                width=70,
                fg_color=COLORS["pink"],
                hover_color=COLORS["pink_hover"],
                text_color=COLORS["text"],
                command=lambda customer_id=customer_id: self.confirm_delete_customer(
                    customer_id
                )
            )

            delete_button.pack(
                side="left"
            )

    def show_add_customer_form(self):
        """Display the Add Customer form."""

        form_window = ctk.CTkToplevel(self)

        form_window.title("Add Customer")
        form_window.geometry("500x600")
        form_window.resizable(False, False)

        form_window.configure(
            fg_color=COLORS["background"]
        )

        # Title
        paw_banner(form_window, "Add Customer", "Enter the customer's information")

        # Form container
        form_frame = ctk.CTkFrame(
            form_window,
            fg_color=COLORS["card"],
            corner_radius=15,
            border_width=2,
            border_color=COLORS["yellow"]
        )

        form_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 30)
        )

        # First Name
        first_name_entry = self.create_form_entry(
            form_frame,
            "First Name",
            "Enter first name"
        )

        # Last Name
        last_name_entry = self.create_form_entry(
            form_frame,
            "Last Name",
            "Enter last name"
        )

        # Contact Number
        contact_entry = self.create_form_entry(
            form_frame,
            "Contact Number",
            "Enter contact number"
        )

        # Email
        email_entry = self.create_form_entry(
            form_frame,
            "Email (Optional)",
            "Enter email address"
        )

        # Address
        address_entry = self.create_form_entry(
            form_frame,
            "Address (Optional)",
            "Enter address"
        )

        # Message label
        message_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=("Arial", 12),
            text_color=COLORS["error"]
        )

        message_label.pack(
            pady=(10, 5)
        )

        # Save button
        save_button = ctk.CTkButton(
            form_frame,
            text="Save Customer",
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            command=lambda: self.save_customer(
                form_window,
                first_name_entry,
                last_name_entry,
                contact_entry,
                email_entry,
                address_entry,
                message_label
            )
        )

        save_button.pack(
            pady=(5, 20)
        )


    def create_form_entry(self, parent, label_text, placeholder):
        """Create a labeled form entry."""

        label = ctk.CTkLabel(
            parent,
            text=label_text,
            text_color=COLORS["text"]
        )

        label.pack(
            fill="x",
            padx=30,
            pady=(15, 3)
        )

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            fg_color=COLORS["input"],
            border_color=COLORS["blue"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted_text"]
        )

        entry.pack(
            fill="x",
            padx=30
        )

        return entry


    def save_customer(
        self,
        form_window,
        first_name_entry,
        last_name_entry,
        contact_entry,
        email_entry,
        address_entry,
        message_label
    ):
        """Validate and save a new customer."""

        first_name = first_name_entry.get().strip()
        last_name = last_name_entry.get().strip()
        contact_number = contact_entry.get().strip()
        email = email_entry.get().strip()
        address = address_entry.get().strip()

        # Required field validation
        if not first_name:
            message_label.configure(
                text="First name is required."
            )
            return

        if not last_name:
            message_label.configure(
                text="Last name is required."
            )
            return

        if not contact_number:
            message_label.configure(
                text="Contact number is required."
            )
            return

        if not 7 <= len(re.sub(r"\D", "", contact_number)) <= 15:
            message_label.configure(text="Enter a valid contact number (7–15 digits).")
            return
        if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            message_label.configure(text="Enter a valid email address or leave it blank.")
            return

        # Save to database
        try:
            add_customer(first_name, last_name, contact_number, email, address)
        except CustomerRuleError as error:
            message_label.configure(text=str(error))
            return

        # Close form
        form_window.destroy()

        # Refresh customer list
        self.load_customers()
        self.show_message("Customer added successfully.")


    def confirm_delete_customer(self, customer_id):
        """Ask for confirmation before deleting a customer."""

        dialog = ctk.CTkToplevel(self)

        dialog.title("Delete Customer")
        dialog.geometry("400x220")
        dialog.resizable(False, False)

        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()

        dialog.configure(
            fg_color=COLORS["background"]
        )

        message = ctk.CTkLabel(
            dialog,
            text="Are you sure you want to delete this customer?\nThis action cannot be undone.",
            font=("Arial", 14),
            text_color=COLORS["text"]
        )

        message.pack(
            pady=(40, 25)
        )

        buttons_frame = ctk.CTkFrame(
            dialog,
            fg_color="transparent"
        )

        buttons_frame.pack()

        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            command=dialog.destroy
        )

        cancel_button.pack(
            side="left",
            padx=5
        )

        confirm_button = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            fg_color=COLORS["pink"],
            hover_color=COLORS["pink_hover"],
            text_color=COLORS["text"],
            command=lambda: self.delete_customer(
                customer_id,
                dialog
            )
        )

        confirm_button.pack(
            side="left",
            padx=5
        )


    def delete_customer(self, customer_id, dialog):
        """Delete a customer and refresh the list."""
        try:
            delete_customer(customer_id)
        except sqlite3.IntegrityError:
            dialog.destroy()
            self.show_message("This customer has pets or appointments and cannot be deleted.")
            return

        dialog.destroy()

        self.load_customers()
        self.show_message("Customer deleted successfully.")


    def show_edit_customer_form(self, customer):
        """Display the Edit Customer form."""

        customer_id, first_name, last_name, contact, email, address, _ = customer

        form_window = ctk.CTkToplevel(self)

        form_window.title("Edit Customer")
        form_window.geometry("500x600")
        form_window.resizable(False, False)

        # Keep popup in front of the main window
        form_window.transient(self.winfo_toplevel())
        form_window.grab_set()
        form_window.lift()
        form_window.focus_force()

        form_window.configure(
            fg_color=COLORS["background"]
        )

        # Title
        paw_banner(form_window, "Edit Customer", "Update the customer's information")

        # Form container
        form_frame = ctk.CTkFrame(
            form_window,
            fg_color=COLORS["card"],
            corner_radius=15,
            border_width=2,
            border_color=COLORS["yellow"]
        )

        form_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 30)
        )

        # First Name
        first_name_entry = self.create_form_entry(
            form_frame,
            "First Name",
            ""
        )
        first_name_entry.insert(0, first_name)

        # Last Name
        last_name_entry = self.create_form_entry(
            form_frame,
            "Last Name",
            ""
        )
        last_name_entry.insert(0, last_name)

        # Contact Number
        contact_entry = self.create_form_entry(
            form_frame,
            "Contact Number",
            ""
        )
        contact_entry.insert(0, contact)

        # Email
        email_entry = self.create_form_entry(
            form_frame,
            "Email (Optional)",
            ""
        )
        if email:
            email_entry.insert(0, email)

        # Address
        address_entry = self.create_form_entry(
            form_frame,
            "Address (Optional)",
            ""
        )
        if address:
            address_entry.insert(0, address)

        # Message label
        message_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=("Arial", 12),
            text_color=COLORS["error"]
        )

        message_label.pack(
            pady=(10, 5)
        )

        # Update button
        update_button = ctk.CTkButton(
            form_frame,
            text="Update Customer",
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            command=lambda: self.update_customer(
                customer_id,
                form_window,
                first_name_entry,
                last_name_entry,
                contact_entry,
                email_entry,
                address_entry,
                message_label
            )
        )

        update_button.pack(
            pady=(5, 20)
        )


    def update_customer(
        self,
        customer_id,
        form_window,
        first_name_entry,
        last_name_entry,
        contact_entry,
        email_entry,
        address_entry,
        message_label
    ):
        """Validate and update a customer."""

        first_name = first_name_entry.get().strip()
        last_name = last_name_entry.get().strip()
        contact_number = contact_entry.get().strip()
        email = email_entry.get().strip()
        address = address_entry.get().strip()

        # Required field validation
        if not first_name:
            message_label.configure(
                text="First name is required."
            )
            return

        if not last_name:
            message_label.configure(
                text="Last name is required."
            )
            return

        if not contact_number:
            message_label.configure(
                text="Contact number is required."
            )
            return

        if not 7 <= len(re.sub(r"\D", "", contact_number)) <= 15:
            message_label.configure(text="Enter a valid contact number (7–15 digits).")
            return
        if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            message_label.configure(text="Enter a valid email address or leave it blank.")
            return

        # Update database
        try:
            update_customer(customer_id, first_name, last_name, contact_number,
                            email, address)
        except CustomerRuleError as error:
            message_label.configure(text=str(error))
            return

        # Close popup
        form_window.destroy()

        # Refresh customer list
        self.load_customers()
        self.show_message("Customer updated successfully.")


    def show_message(self, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Customers")
        dialog.geometry("400x180")
        dialog.transient(self.winfo_toplevel())
        dialog.configure(fg_color=COLORS["background"])
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=message, text_color=COLORS["text"],
                     wraplength=350).pack(pady=28)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy,
                      fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"]).pack()
