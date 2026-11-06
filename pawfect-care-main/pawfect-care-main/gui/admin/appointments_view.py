import sqlite3
from datetime import date, datetime

import customtkinter as ctk

from services.appointment_service import (
    AppointmentRuleError,
    STATUS_TRANSITIONS,
    cancel_appointment,
    create_appointment,
    delete_appointment,
    get_all_appointments,
    get_appointment_service_ids,
    get_active_groomers,
    get_customer_pets,
    get_services_for_appointment,
    register_walk_in_visit,
    update_appointment,
    update_appointment_status,
)
from services.customer_service import get_all_customers
from services.dashboard_service import APPOINTMENT_STATUSES
from utils.theme import COLORS
from utils.decor import bind_date_mask, bind_time_mask, paw_banner


class AppointmentsView(ctk.CTkFrame):
    """Admin appointment list, booking form, and lifecycle actions."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["background"])
        self.create_widgets()
        self.load_appointments()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="Appointments / Visits", font=("Arial", 30, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Manage scheduled bookings and walk-in visits",
                     font=("Arial", 14), text_color=COLORS["muted_text"]).pack(anchor="w")
        header_actions = ctk.CTkFrame(header, fg_color="transparent")
        header_actions.pack(side="right", pady=10)
        ctk.CTkButton(header_actions, text="Register Walk-in Visit", fg_color=COLORS["pink"],
                      hover_color=COLORS["pink_hover"], text_color=COLORS["text"],
                      command=self.show_walk_in_form).pack(side="left", padx=(0, 8))
        ctk.CTkButton(header_actions, text="+ Add Appointment", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"],
                      command=self.show_add_form).pack(side="left")
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=30, pady=(0, 12))
        self.search_entry = ctk.CTkEntry(
            filters, placeholder_text="Search appointment, pet, customer, or service",
            fg_color=COLORS["input"], border_color=COLORS["blue"], text_color=COLORS["text"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _event: self.load_appointments())
        self.status_filter = ctk.CTkOptionMenu(
            filters, values=["All statuses", *APPOINTMENT_STATUSES],
            fg_color=COLORS["blue"], button_color=COLORS["blue_hover"],
            command=lambda _value: self.load_appointments()
        )
        self.status_filter.pack(side="right", padx=(6, 0))
        self.date_filter = ctk.CTkOptionMenu(
            filters, values=["All dates", "Today", "Upcoming", "Past"],
            fg_color=COLORS["blue"], button_color=COLORS["blue_hover"],
            command=lambda _value: self.load_appointments()
        )
        self.date_filter.pack(side="right", padx=(6, 0))
        self.type_filter = ctk.CTkOptionMenu(
            filters, values=["All types", "Appointments", "Walk-in Visits"],
            fg_color=COLORS["blue"], button_color=COLORS["blue_hover"],
            command=lambda _value: self.load_appointments()
        )
        self.type_filter.pack(side="right", padx=(6, 0))
        self.status_filter.set("All statuses")
        self.date_filter.set("All dates")
        self.type_filter.set("All types")
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 25))

    def load_appointments(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        appointments = get_all_appointments()
        query = self.search_entry.get().strip().casefold()
        selected_status = self.status_filter.get()
        date_filter = self.date_filter.get()
        type_filter = self.type_filter.get()
        today = date.today().isoformat()
        appointments = [appointment for appointment in appointments
                        if (selected_status == "All statuses" or appointment[8] == selected_status)
                        and (date_filter == "All dates"
                             or (date_filter == "Today" and appointment[6] == today)
                             or (date_filter == "Upcoming" and appointment[6] >= today
                                 and appointment[8] not in ("Completed", "Cancelled"))
                             or (date_filter == "Past" and appointment[6] < today))
                        and (type_filter == "All types"
                             or (type_filter == "Appointments" and appointment[13] == "Appointment")
                             or (type_filter == "Walk-in Visits" and appointment[13] == "Walk-in Visit"))
                        and (not query or query in " ".join(
                            str(value or "") for value in (
                                appointment[1], appointment[3], appointment[5],
                                appointment[8], appointment[9], appointment[10], appointment[13],
                                appointment[15]
                            )
                        ).casefold())]
        if not appointments:
            ctk.CTkLabel(self.list_frame, text="No appointments found. Add an appointment to get started.",
                         font=("Arial", 16), text_color=COLORS["muted_text"]).pack(pady=50)
            return

        for appointment in appointments:
            (appointment_id, number, pet_id, pet_name, customer_id, customer_name,
             appt_date, appt_time, status, notes, service_names, total, has_payment,
             appointment_type, groomer_id, groomer_name) = appointment
            card = ctk.CTkFrame(self.list_frame, fg_color=COLORS["card"], corner_radius=12)
            card.pack(fill="x", pady=6)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=15, pady=(12, 2))
            ctk.CTkLabel(top, text=f"{number}  •  {pet_name} ({customer_name})",
                         font=("Arial", 15, "bold"), text_color=COLORS["text"]).pack(side="left", anchor="w")
            ctk.CTkLabel(top, text=status, font=("Arial", 12, "bold"),
                         text_color=COLORS["blue"] if status != "Cancelled" else COLORS["error"]).pack(side="right")
            ctk.CTkLabel(top, text=appointment_type, font=("Arial", 11),
                         text_color=COLORS["muted_text"]).pack(side="right", padx=10)
            details = (f"{appt_date} at {appt_time}   |   {service_names or 'No services'}   |   "
                       f"₱{total:,.2f}   |   Groomer: {groomer_name or 'Unassigned'}")
            ctk.CTkLabel(card, text=details, text_color=COLORS["muted_text"],
                         anchor="w", wraplength=850).pack(fill="x", padx=15, pady=(1, 5))
            if notes:
                ctk.CTkLabel(card, text=f"Notes: {notes}", text_color=COLORS["muted_text"],
                             anchor="w", wraplength=850).pack(fill="x", padx=15, pady=(0, 4))

            has_actions = (
                status in ("Pending", "Confirmed", "In Progress", "Cancelled")
                or (status in ("Completed", "Cancelled") and has_payment)
            )
            if has_actions:
                actions = ctk.CTkFrame(card, fg_color="transparent", height=36)
                actions.pack(fill="x", padx=10, pady=(2, 10))
                actions.pack_propagate(False)
            if status in ("Pending", "Confirmed"):
                ctk.CTkButton(actions, text="Edit", width=70, fg_color=COLORS["yellow"],
                              hover_color=COLORS["yellow_hover"], text_color=COLORS["text"],
                              command=lambda record=appointment: self.show_edit_form(record)).pack(side="left", padx=4)
                ctk.CTkButton(actions, text="Update Status", width=110, fg_color=COLORS["blue"],
                              hover_color=COLORS["blue_hover"],
                              command=lambda record=appointment: self.show_status_form(record)).pack(side="left", padx=4)
                ctk.CTkButton(actions, text="Cancel", width=70, fg_color=COLORS["pink"],
                              hover_color=COLORS["pink_hover"], text_color=COLORS["text"],
                              command=lambda record=appointment: self.confirm_cancel(record)).pack(side="left", padx=4)
            elif status == "In Progress":
                ctk.CTkButton(actions, text="Update Status", width=110, fg_color=COLORS["blue"],
                              hover_color=COLORS["blue_hover"],
                              command=lambda record=appointment: self.show_status_form(record)).pack(side="left", padx=4)
            elif status == "Cancelled":
                text = "Delete" if not has_payment else "Paid · Keep Record"
                button = ctk.CTkButton(actions, text=text, width=125,
                                       fg_color=COLORS["pink"] if not has_payment else COLORS["muted_text"],
                                       hover_color=COLORS["pink_hover"] if not has_payment else COLORS["muted_text"],
                                       text_color=COLORS["text"])
                if not has_payment:
                    button.configure(command=lambda record=appointment: self.confirm_delete(record))
                button.pack(side="left", padx=4)
            if status in ("Completed", "Cancelled") and has_payment:
                ctk.CTkLabel(actions, text="Payment recorded", text_color=COLORS["muted_text"]).pack(side="left", padx=6)

    def show_add_form(self):
        self.show_appointment_form()

    def show_walk_in_form(self):
        self.show_appointment_form(walk_in=True)

    def show_edit_form(self, appointment):
        self.show_appointment_form(appointment)

    def show_appointment_form(self, appointment=None, walk_in=False):
        customers = get_all_customers()
        if not customers:
            self.show_message("Add a customer before scheduling an appointment.")
            return
        appointment_id = appointment[0] if appointment else None
        services = get_services_for_appointment(appointment_id)
        if not services:
            self.show_message("Add an active service before scheduling an appointment.")
            return

        window = ctk.CTkToplevel(self)
        editing = appointment is not None
        window.title("Edit Appointment" if editing else
                     "Register Walk-in Visit" if walk_in else "Add Appointment")
        window.geometry("590x780")
        window.minsize(520, 600)
        window.transient(self.winfo_toplevel())
        window.grab_set()
        window.configure(fg_color=COLORS["background"])
        paw_banner(window, "Edit Appointment" if editing else
                   "Register Walk-in Visit" if walk_in else "Add Appointment",
                   "Pick the pet, groomer, and services")
        form = ctk.CTkScrollableFrame(window, fg_color=COLORS["card"], corner_radius=15,
                                      border_width=2, border_color=COLORS["yellow"])
        form.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        customer_options = {f"{c[0]} — {c[1]} {c[2]}": c[0] for c in customers}
        customer_by_id = {c[0]: f"{c[0]} — {c[1]} {c[2]}" for c in customers}
        self._form_pet_options = {}
        self._form_pet_menu = None
        self._form_pet_message = None

        ctk.CTkLabel(form, text="Customer", text_color=COLORS["text"]).pack(anchor="w", padx=22, pady=(12, 3))
        customer_menu = ctk.CTkOptionMenu(
            form, values=list(customer_options), fg_color=COLORS["blue"],
            button_color=COLORS["blue_hover"],
            command=lambda selected: self.populate_pet_menu(customer_options[selected])
        )
        customer_menu.pack(fill="x", padx=22)
        ctk.CTkLabel(form, text="Customer's Pet", text_color=COLORS["text"]).pack(anchor="w", padx=22, pady=(12, 3))
        pet_menu = ctk.CTkOptionMenu(form, values=["Select a customer"], fg_color=COLORS["blue"],
                                     button_color=COLORS["blue_hover"])
        pet_menu.pack(fill="x", padx=22)
        self._form_pet_menu = pet_menu
        pet_message = ctk.CTkLabel(form, text="", text_color=COLORS["muted_text"])
        pet_message.pack(anchor="w", padx=22, pady=(2, 0))
        self._form_pet_message = pet_message

        groomers = get_active_groomers()
        if editing and appointment[14] and appointment[14] not in {g[0] for g in groomers}:
            groomers = [*groomers, (appointment[14], appointment[15])]
        self._form_groomer_options = {"Unassigned": None}
        self._form_groomer_options.update({f"{gid} — {name}": gid for gid, name in groomers})
        ctk.CTkLabel(form, text="Assigned Groomer", text_color=COLORS["text"]).pack(
            anchor="w", padx=22, pady=(12, 3))
        groomer_menu = ctk.CTkOptionMenu(
            form, values=list(self._form_groomer_options), fg_color=COLORS["blue"],
            button_color=COLORS["blue_hover"]
        )
        groomer_menu.pack(fill="x", padx=22)
        groomer_menu.set("Unassigned")
        if editing and appointment[14]:
            for label, gid in self._form_groomer_options.items():
                if gid == appointment[14]:
                    groomer_menu.set(label)
        self._form_groomer_menu = groomer_menu

        ctk.CTkLabel(form, text="Services (select one or more)", text_color=COLORS["text"]).pack(
            anchor="w", padx=22, pady=(12, 3))
        service_checks = {}
        current_services = set(get_appointment_service_ids(appointment_id)) if editing else set()
        for service_id, name, price, duration in services:
            check = ctk.CTkCheckBox(
                form, text=f"{name}  ·  ₱{price:,.2f}  ·  {duration} min",
                text_color=COLORS["text"], fg_color=COLORS["blue"],
                hover_color=COLORS["blue_hover"]
            )
            check.pack(anchor="w", padx=22, pady=4)
            if service_id in current_services:
                check.select()
            service_checks[service_id] = check

        if walk_in:
            ctk.CTkLabel(form, text="The visit will be timestamped now and start as In Progress.",
                         text_color=COLORS["muted_text"]).pack(anchor="w", padx=22, pady=(14, 4))
            date_entry = time_entry = None
        else:
            date_entry = self.create_entry(form, "Date (YYYY-MM-DD)", "YYYY-MM-DD")
            time_entry = self.create_entry(form, "Time (24-hour HH:MM)", "HH:MM")
            bind_date_mask(date_entry)
            bind_time_mask(time_entry)
        notes_entry = self.create_entry(form, "Notes (optional)", "Special instructions")
        if editing:
            customer_id = appointment[4]
            customer_menu.set(customer_by_id.get(customer_id, list(customer_options)[0]))
            self.populate_pet_menu(customer_id)
            date_entry.insert(0, appointment[6])
            time_entry.insert(0, appointment[7])
            if appointment[9]:
                notes_entry.insert(0, appointment[9])
        else:
            customer_menu.set(list(customer_options)[0])
            self.populate_pet_menu(next(iter(customer_options.values())))

        error_label = ctk.CTkLabel(form, text="", text_color=COLORS["error"], wraplength=440)
        error_label.pack(pady=(12, 4))
        ctk.CTkButton(
            form, text="Update Appointment" if editing else "Save Appointment",
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            command=lambda: self.save_appointment(
                window, appointment_id, pet_menu, walk_in,
                service_checks, date_entry, time_entry, notes_entry, error_label
            )
        ).pack(pady=(8, 18))

    def populate_pet_menu(self, customer_id):
        pets = get_customer_pets(customer_id)
        options = {f"{pet_id} — {name} ({species})": pet_id for pet_id, name, species in pets}
        self._form_pet_options = options
        if options:
            self._form_pet_menu.configure(values=list(options), state="normal")
            if self._form_pet_menu.get() not in options:
                self._form_pet_menu.set(list(options)[0])
            self._form_pet_message.configure(text="")
        else:
            self._form_pet_menu.configure(values=["No pets for this customer"], state="disabled")
            self._form_pet_menu.set("No pets for this customer")
            self._form_pet_message.configure(text="Add a pet to this customer's record first.")

    def create_entry(self, parent, label, placeholder):
        ctk.CTkLabel(parent, text=label, text_color=COLORS["text"]).pack(
            anchor="w", padx=22, pady=(12, 3))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder,
                             fg_color=COLORS["input"], border_color=COLORS["blue"],
                             text_color=COLORS["text"])
        entry.pack(fill="x", padx=22)
        return entry

    def save_appointment(self, window, appointment_id, pet_menu, walk_in, service_checks, date_entry, time_entry,
                         notes_entry, error_label):
        date_text = time_text = None
        if not walk_in:
            try:
                date_text = date_entry.get().strip()
                time_text = time_entry.get().strip()
                appointment_date = datetime.strptime(date_text, "%Y-%m-%d").date()
                appointment_time = datetime.strptime(time_text, "%H:%M").time()
                if datetime.combine(appointment_date, appointment_time) < datetime.now():
                    raise ValueError("Appointments cannot be scheduled in the past.")
            except ValueError as error:
                error_label.configure(text=str(error) or "Use date YYYY-MM-DD and time HH:MM.")
                return
        service_ids = [service_id for service_id, checkbox in service_checks.items()
                       if checkbox.get()]
        if not service_ids:
            error_label.configure(text="Select at least one service.")
            return
        pet_id = self._form_pet_options.get(pet_menu.get())
        if pet_id is None:
            error_label.configure(text="Select a pet that belongs to the chosen customer.")
            return
        groomer_id = self._form_groomer_options.get(self._form_groomer_menu.get())
        try:
            if walk_in:
                register_walk_in_visit(pet_id, notes_entry.get(), service_ids, groomer_id)
            elif appointment_id is None:
                create_appointment(pet_id, date_text, time_text, notes_entry.get(),
                                   service_ids, groomer_id)
            else:
                update_appointment(appointment_id, pet_id, date_text, time_text,
                                   notes_entry.get(), service_ids, groomer_id)
        except (AppointmentRuleError, sqlite3.IntegrityError) as error:
            error_label.configure(text=str(error))
            return
        window.destroy()
        self.load_appointments()
        self.show_message("Walk-in visit registered." if walk_in else
                          "Appointment updated." if appointment_id is not None else
                          "Appointment created.")

    def show_status_form(self, appointment):
        appointment_id, number, _, pet_name, _, _, _, _, current_status = appointment[:9]
        allowed = sorted(STATUS_TRANSITIONS[current_status] - {"Cancelled"})
        if not allowed:
            self.show_message(f"{current_status} appointments cannot change status.")
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title("Update Appointment Status")
        dialog.geometry("430x260")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        ctk.CTkLabel(dialog, text=f"{number} · {pet_name}", font=("Arial", 16, "bold"),
                     text_color=COLORS["text"]).pack(pady=(25, 12))
        ctk.CTkLabel(dialog, text=f"Current status: {current_status}",
                     text_color=COLORS["muted_text"]).pack(pady=4)
        menu = ctk.CTkOptionMenu(dialog, values=allowed, fg_color=COLORS["blue"],
                                 button_color=COLORS["blue_hover"])
        menu.pack(pady=10)
        menu.set(allowed[0])
        error_label = ctk.CTkLabel(dialog, text="", text_color=COLORS["error"])
        error_label.pack()
        ctk.CTkButton(dialog, text="Save Status", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"],
                      command=lambda: self.save_status(appointment_id, menu.get(), dialog, error_label)).pack(pady=10)

    def save_status(self, appointment_id, status, dialog, error_label):
        try:
            update_appointment_status(appointment_id, status)
        except AppointmentRuleError as error:
            error_label.configure(text=str(error))
            return
        dialog.destroy()
        self.load_appointments()
        self.show_message(f"Appointment status updated to {status}.")

    def confirm_cancel(self, appointment):
        appointment_id, number = appointment[0], appointment[1]
        self.confirm_action(
            "Cancel Appointment", f"Cancel appointment {number}?",
            lambda dialog, error: self.run_cancel(appointment_id, dialog, error)
        )

    def run_cancel(self, appointment_id, dialog, error_label):
        try:
            cancel_appointment(appointment_id)
        except AppointmentRuleError as error:
            error_label.configure(text=str(error))
            return
        dialog.destroy()
        self.load_appointments()
        self.show_message("Appointment cancelled.")

    def confirm_delete(self, appointment):
        appointment_id, number = appointment[0], appointment[1]
        self.confirm_action(
            "Delete Appointment", f"Permanently delete cancelled appointment {number}?",
            lambda dialog, error: self.run_delete(appointment_id, dialog, error)
        )

    def run_delete(self, appointment_id, dialog, error_label):
        try:
            delete_appointment(appointment_id)
        except AppointmentRuleError as error:
            error_label.configure(text=str(error))
            return
        dialog.destroy()
        self.load_appointments()
        self.show_message("Cancelled appointment deleted.")

    def confirm_action(self, title, message, action):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("430x240")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        ctk.CTkLabel(dialog, text=message, font=("Arial", 14),
                     text_color=COLORS["text"], wraplength=370).pack(pady=(30, 14))
        error_label = ctk.CTkLabel(dialog, text="", text_color=COLORS["error"], wraplength=380)
        error_label.pack(pady=4)
        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(pady=8)
        ctk.CTkButton(buttons, text="Keep", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"], command=dialog.destroy).pack(side="left", padx=5)
        ctk.CTkButton(buttons, text="Confirm", fg_color=COLORS["pink"],
                      hover_color=COLORS["pink_hover"], text_color=COLORS["text"],
                      command=lambda: action(dialog, error_label)).pack(side="left", padx=5)

    def show_message(self, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Appointments")
        dialog.geometry("400x180")
        dialog.transient(self.winfo_toplevel())
        dialog.configure(fg_color=COLORS["background"])
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=message, text_color=COLORS["text"],
                     wraplength=350).pack(pady=30)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy,
                      fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"]).pack()
