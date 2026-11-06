import sqlite3

import customtkinter as ctk

from services.payment_service import (
    PAYMENT_METHODS,
    PAYMENT_STATUSES,
    PAYMENT_TRANSITIONS,
    PaymentRuleError,
    calculate_appointment_total,
    get_all_payments,
    get_payable_appointments,
    record_payment,
    update_payment_status,
)
from utils.theme import COLORS


class PaymentsView(ctk.CTkFrame):
    """Admin page for recording and tracking payments."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["background"])
        self.create_widgets()
        self.load_payments()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="Payments", font=("Arial", 30, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Record payments and track payment status",
                     font=("Arial", 14), text_color=COLORS["muted_text"]).pack(anchor="w")
        ctk.CTkButton(header, text="+ Record Payment", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"],
                      command=self.show_record_form).pack(side="right", pady=10)
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=30, pady=(0, 12))
        self.search_entry = ctk.CTkEntry(
            filters, placeholder_text="Search payment, appointment, customer, or pet",
            fg_color=COLORS["input"], border_color=COLORS["blue"], text_color=COLORS["text"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _event: self.load_payments())
        self.status_filter = ctk.CTkOptionMenu(
            filters, values=["All statuses", *PAYMENT_STATUSES],
            fg_color=COLORS["blue"], button_color=COLORS["blue_hover"],
            command=lambda _value: self.load_payments()
        )
        self.status_filter.pack(side="right", padx=(6, 0))
        self.method_filter = ctk.CTkOptionMenu(
            filters, values=["All methods", *PAYMENT_METHODS],
            fg_color=COLORS["blue"], button_color=COLORS["blue_hover"],
            command=lambda _value: self.load_payments()
        )
        self.method_filter.pack(side="right", padx=(6, 0))
        self.status_filter.set("All statuses")
        self.method_filter.set("All methods")
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 25))

    def load_payments(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        payments = get_all_payments()
        query = self.search_entry.get().strip().casefold()
        selected_status = self.status_filter.get()
        selected_method = self.method_filter.get()
        payments = [payment for payment in payments
                    if (selected_status == "All statuses" or payment[9] == selected_status)
                    and (selected_method == "All methods" or payment[8] == selected_method)
                    and (not query or query in " ".join(
                        str(value or "") for value in payment[2:11]
                    ).casefold())]
        if not payments:
            ctk.CTkLabel(self.list_frame, text="No payments recorded yet.",
                         font=("Arial", 16), text_color=COLORS["muted_text"]).pack(pady=50)
            return

        for payment in payments:
            (payment_id, appointment_id, appointment_number, customer_name,
             pet_name, appt_date, appt_time, amount, method, status,
             payment_date) = payment
            card = ctk.CTkFrame(self.list_frame, fg_color=COLORS["card"], corner_radius=12)
            card.pack(fill="x", pady=6)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=15, pady=(12, 2))
            ctk.CTkLabel(top, text=f"{appointment_number}  ·  {pet_name} ({customer_name})",
                         font=("Arial", 15, "bold"), text_color=COLORS["text"]).pack(side="left", anchor="w")
            ctk.CTkLabel(top, text=status, font=("Arial", 12, "bold"),
                         text_color=COLORS["error"] if status == "Refunded" else COLORS["blue"]).pack(side="right")
            details = (f"₱{amount:,.2f}   |   {method}   |   Appointment: {appt_date} at {appt_time}"
                       f"   |   Recorded: {payment_date}")
            ctk.CTkLabel(card, text=details, text_color=COLORS["muted_text"],
                         anchor="w", wraplength=850).pack(fill="x", padx=15, pady=(2, 8))
            if PAYMENT_TRANSITIONS.get(status):
                actions = ctk.CTkFrame(card, fg_color="transparent", height=36)
                actions.pack(fill="x", padx=10, pady=(0, 8))
                actions.pack_propagate(False)
                ctk.CTkButton(actions, text="Update Status", width=115,
                              fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
                              command=lambda record=payment: self.show_status_form(record)).pack(
                                  side="left", padx=4)

    def show_record_form(self):
        appointments = get_payable_appointments()
        if not appointments:
            self.show_message("There are no completed unpaid appointments to record.")
            return

        window = ctk.CTkToplevel(self)
        window.title("Record Payment")
        window.geometry("500x440")
        window.resizable(False, False)
        window.transient(self.winfo_toplevel())
        window.grab_set()
        window.configure(fg_color=COLORS["background"])
        ctk.CTkLabel(window, text="Record Payment", font=("Arial", 25, "bold"),
                     text_color=COLORS["blue"]).pack(pady=(22, 12))
        form = ctk.CTkFrame(window, fg_color=COLORS["card"], corner_radius=15)
        form.pack(fill="both", expand=True, padx=25, pady=(0, 22))

        appointment_options = {}
        for item in appointments:
            appointment_id, number, appt_date, appt_time, pet, customer, total, service_count = item
            label = f"{number} — {pet} ({customer}) · {appt_date} {appt_time}"
            appointment_options[label] = item
        ctk.CTkLabel(form, text="Completed Appointment", text_color=COLORS["text"]).pack(
            anchor="w", padx=25, pady=(18, 4))
        appointment_menu = ctk.CTkOptionMenu(
            form, values=list(appointment_options), fg_color=COLORS["blue"],
            button_color=COLORS["blue_hover"]
        )
        appointment_menu.pack(fill="x", padx=25)

        total_label = ctk.CTkLabel(form, text="Total: ₱0.00", font=("Arial", 18, "bold"),
                                   text_color=COLORS["text"])
        total_label.pack(anchor="w", padx=25, pady=(18, 8))

        ctk.CTkLabel(form, text="Payment Method", text_color=COLORS["text"]).pack(
            anchor="w", padx=25, pady=(8, 4))
        method_menu = ctk.CTkOptionMenu(form, values=list(PAYMENT_METHODS),
                                        fg_color=COLORS["blue"], button_color=COLORS["blue_hover"])
        method_menu.pack(fill="x", padx=25)
        method_menu.set("Cash")

        ctk.CTkLabel(form, text="Initial Status", text_color=COLORS["text"]).pack(
            anchor="w", padx=25, pady=(12, 4))
        status_menu = ctk.CTkOptionMenu(form, values=["Paid", "Pending"],
                                        fg_color=COLORS["blue"], button_color=COLORS["blue_hover"])
        status_menu.pack(fill="x", padx=25)
        status_menu.set("Paid")
        error_label = ctk.CTkLabel(form, text="", text_color=COLORS["error"], wraplength=400)
        error_label.pack(pady=(8, 2))

        def refresh_total(selected):
            item = appointment_options[selected]
            amount = calculate_appointment_total(item[0])
            total_label.configure(text=f"Total: ₱{amount:,.2f}")

        appointment_menu.configure(command=refresh_total)
        first_option = list(appointment_options)[0]
        appointment_menu.set(first_option)
        refresh_total(first_option)
        ctk.CTkButton(
            form, text="Save Payment", fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            command=lambda: self.save_payment(window, appointment_options[appointment_menu.get()][0],
                                              method_menu.get(), status_menu.get(), error_label)
        ).pack(pady=(8, 18))

    def save_payment(self, window, appointment_id, method, status, error_label):
        try:
            record_payment(appointment_id, method, status)
        except (PaymentRuleError, sqlite3.IntegrityError) as error:
            error_label.configure(text=str(error))
            return
        window.destroy()
        self.load_payments()
        self.show_message("Payment recorded successfully.")

    def show_status_form(self, payment):
        payment_id, _, appointment_number, customer, pet, _, _, amount, method, current_status, _ = payment
        allowed = sorted(PAYMENT_TRANSITIONS[current_status])
        if not allowed:
            self.show_message(f"{current_status} payments cannot change status.")
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title("Update Payment Status")
        dialog.geometry("460x330")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        ctk.CTkLabel(dialog, text=f"{appointment_number} · {pet} ({customer})",
                     font=("Arial", 15, "bold"), text_color=COLORS["text"]).pack(pady=(22, 8))
        ctk.CTkLabel(dialog, text=f"₱{amount:,.2f} · {method} · Current status: {current_status}",
                     text_color=COLORS["muted_text"]).pack(pady=4)
        ctk.CTkLabel(dialog, text="Refunded records are retained for the audit trail.",
                     text_color=COLORS["muted_text"]).pack(pady=(12, 4))
        status_menu = ctk.CTkOptionMenu(dialog, values=allowed, fg_color=COLORS["blue"],
                                        button_color=COLORS["blue_hover"])
        status_menu.pack(pady=8)
        status_menu.set(allowed[0])
        refund_confirm = None
        if "Refunded" in allowed:
            refund_confirm = ctk.CTkCheckBox(
                dialog, text="I confirm this payment was refunded",
                text_color=COLORS["text"], fg_color=COLORS["blue"],
                hover_color=COLORS["blue_hover"]
            )
            refund_confirm.pack(pady=5)
        error_label = ctk.CTkLabel(dialog, text="", text_color=COLORS["error"])
        error_label.pack()
        ctk.CTkButton(dialog, text="Save Status", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"],
                      command=lambda: self.save_status(payment_id, status_menu.get(), dialog,
                                                       error_label, refund_confirm)).pack(pady=10)

    def save_status(self, payment_id, status, dialog, error_label, refund_confirm):
        if status == "Refunded" and (refund_confirm is None or not refund_confirm.get()):
            error_label.configure(text="Confirm the refund before updating this payment.")
            return
        try:
            update_payment_status(payment_id, status)
        except PaymentRuleError as error:
            error_label.configure(text=str(error))
            return
        dialog.destroy()
        self.load_payments()
        self.show_message(f"Payment status updated to {status}.")

    def show_message(self, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Payments")
        dialog.geometry("400x180")
        dialog.transient(self.winfo_toplevel())
        dialog.configure(fg_color=COLORS["background"])
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=message, text_color=COLORS["text"],
                     wraplength=350).pack(pady=30)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy,
                      fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"]).pack()
