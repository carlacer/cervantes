import sqlite3
import math
from datetime import date

import customtkinter as ctk

from services.customer_service import get_all_customers
from services.pet_service import add_pet, delete_pet, get_all_pets, update_pet
from utils.theme import COLORS
from utils.decor import bind_date_mask, paw_banner


class PetsView(ctk.CTkFrame):
    """Admin page for viewing and managing pets and their owners."""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["background"])
        self.create_widgets()
        self.load_pets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="Pets", font=("Arial", 30, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Manage pets and assign them to customers",
                     font=("Arial", 14), text_color=COLORS["muted_text"]).pack(anchor="w")

        ctk.CTkButton(header, text="+ Add Pet", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"],
                      command=self.show_add_pet_form).pack(side="right", pady=10)

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=30, pady=(0, 12))
        self.search_entry = ctk.CTkEntry(
            filters, placeholder_text="Search pet, breed, species, or owner",
            fg_color=COLORS["input"], border_color=COLORS["blue"], text_color=COLORS["text"]
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _event: self.load_pets())
        self.species_filter = ctk.CTkOptionMenu(
            filters, values=["All species"], fg_color=COLORS["blue"],
            button_color=COLORS["blue_hover"], command=lambda _value: self.load_pets()
        )
        self.species_filter.pack(side="right")
        self.species_filter.set("All species")

        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=COLORS["card"], corner_radius=15
        )
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def load_pets(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        pets = get_all_pets()
        species_values = ["All species"] + sorted({pet[3] for pet in pets})
        current_species = self.species_filter.get()
        self.species_filter.configure(values=species_values)
        if current_species not in species_values:
            self.species_filter.set("All species")
        query = self.search_entry.get().strip().casefold()
        selected_species = self.species_filter.get()
        pets = [pet for pet in pets
                if (selected_species == "All species" or pet[3] == selected_species)
                and (not query or query in " ".join(
                    str(value or "") for value in (pet[2], pet[3], pet[4], pet[9], pet[10])
                ).casefold())]
        headers = ("ID", "Pet", "Species / Breed", "Gender", "Owner", "Actions")
        for column, text in enumerate(headers):
            self.list_frame.grid_columnconfigure(column, weight=1 if column != 5 else 2)
            ctk.CTkLabel(self.list_frame, text=text, font=("Arial", 12, "bold"),
                         fg_color=COLORS["yellow"], text_color=COLORS["text"],
                         corner_radius=8).grid(row=0, column=column, sticky="ew",
                                               padx=2, pady=(10, 10))

        if not pets:
            empty = ctk.CTkLabel(
                self.list_frame, text="No pets found. Add a pet to get started.",
                font=("Arial", 16), text_color=COLORS["muted_text"]
            )
            empty.grid(row=1, column=0, columnspan=6, pady=50)
            return

        for row, pet in enumerate(pets, start=1):
            (pet_id, customer_id, name, species, breed, gender, dob, weight,
             notes, first_name, last_name) = pet
            values = (pet_id, name, f"{species} / {breed or '-'}", gender or "Unknown",
                      f"{first_name} {last_name}")
            for column, value in enumerate(values):
                ctk.CTkLabel(self.list_frame, text=str(value),
                             text_color=COLORS["text"]).grid(
                    row=row, column=column, sticky="ew", padx=5, pady=10
                )
            actions = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            actions.grid(row=row, column=5, padx=5, pady=5)
            ctk.CTkButton(actions, text="Edit", width=65, fg_color=COLORS["yellow"],
                          hover_color=COLORS["yellow_hover"], text_color=COLORS["text"],
                          command=lambda record=pet: self.show_pet_form(record)).pack(
                              side="left", padx=(0, 5))
            ctk.CTkButton(actions, text="Delete", width=65, fg_color=COLORS["pink"],
                          hover_color=COLORS["pink_hover"], text_color=COLORS["text"],
                          command=lambda record_id=pet_id: self.confirm_delete(record_id)).pack(
                              side="left")

    def show_add_pet_form(self):
        self.show_pet_form()

    def show_pet_form(self, pet=None):
        customers = get_all_customers()
        if not customers:
            self.show_message("Add a customer before registering a pet.")
            return

        window = ctk.CTkToplevel(self)
        is_edit = pet is not None
        window.title("Edit Pet" if is_edit else "Add Pet")
        window.geometry("520x720")
        window.minsize(480, 580)
        window.transient(self.winfo_toplevel())
        window.grab_set()
        window.configure(fg_color=COLORS["background"])

        paw_banner(window, "Edit Pet" if is_edit else "Add Pet",
                   "Tell us about the furry friend")
        form = ctk.CTkScrollableFrame(window, fg_color=COLORS["card"], corner_radius=15,
                                      border_width=2, border_color=COLORS["yellow"])
        form.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        customer_options = {
            f"{item[0]} — {item[1]} {item[2]}": item[0] for item in customers
        }
        ctk.CTkLabel(form, text="Customer (Owner)", text_color=COLORS["text"]).pack(
            anchor="w", padx=25, pady=(15, 3))
        owner_menu = ctk.CTkOptionMenu(form, values=list(customer_options),
                                       fg_color=COLORS["blue"], button_color=COLORS["blue_hover"])
        owner_menu.pack(fill="x", padx=25)

        fields = {}
        specs = [
            ("Pet Name", "pet_name", "Required"),
            ("Species", "species", "e.g. Dog, Cat"),
            ("Breed", "breed", "Optional"),
            ("Date of Birth", "date_of_birth", "YYYY-MM-DD (optional)"),
            ("Weight (kg)", "weight", "Optional"),
            ("Special Notes", "special_notes", "Optional"),
        ]
        for label_text, key, placeholder in specs:
            ctk.CTkLabel(form, text=label_text, text_color=COLORS["text"]).pack(
                anchor="w", padx=25, pady=(12, 3))
            entry = ctk.CTkEntry(form, placeholder_text=placeholder,
                                 fg_color=COLORS["input"], border_color=COLORS["blue"],
                                 text_color=COLORS["text"])
            entry.pack(fill="x", padx=25)
            fields[key] = entry
        bind_date_mask(fields["date_of_birth"])

        ctk.CTkLabel(form, text="Gender", text_color=COLORS["text"]).pack(
            anchor="w", padx=25, pady=(12, 3))
        gender_menu = ctk.CTkOptionMenu(form, values=["Unknown", "Female", "Male"],
                                        fg_color=COLORS["blue"], button_color=COLORS["blue_hover"])
        gender_menu.pack(fill="x", padx=25)

        error_label = ctk.CTkLabel(form, text="", text_color=COLORS["error"], wraplength=400)
        error_label.pack(pady=(12, 4))

        if is_edit:
            pet_id, current_customer, name, species, breed, gender, dob, weight, notes = pet[:9]
            selected = next((option for option, cid in customer_options.items()
                             if cid == current_customer), list(customer_options)[0])
            owner_menu.set(selected)
            initial = {"pet_name": name, "species": species, "breed": breed or "",
                       "date_of_birth": dob or "", "weight": "" if weight is None else str(weight),
                       "special_notes": notes or ""}
            for key, value in initial.items():
                fields[key].insert(0, value)
            gender_menu.set(gender or "Unknown")
        else:
            pet_id = None
            owner_menu.set(list(customer_options)[0])

        ctk.CTkButton(
            form, text="Update Pet" if is_edit else "Save Pet", fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            command=lambda: self.save_pet(window, pet_id, owner_menu, customer_options,
                                          fields, gender_menu, error_label)
        ).pack(pady=(8, 20))

    def save_pet(self, window, pet_id, owner_menu, customer_options, fields,
                 gender_menu, error_label):
        name = fields["pet_name"].get().strip()
        species = fields["species"].get().strip()
        if not name or not species:
            error_label.configure(text="Pet name and species are required.")
            return
        raw_weight = fields["weight"].get().strip()
        try:
            weight = float(raw_weight) if raw_weight else None
            if weight is not None and (not math.isfinite(weight) or weight <= 0):
                raise ValueError
        except ValueError:
            error_label.configure(text="Weight must be a number greater than zero.")
            return

        raw_dob = fields["date_of_birth"].get().strip()
        if raw_dob:
            try:
                dob = date.fromisoformat(raw_dob)
                if dob > date.today():
                    raise ValueError
            except ValueError:
                error_label.configure(text="Enter a valid birth date (YYYY-MM-DD) that is not in the future.")
                return

        try:
            customer_id = customer_options[owner_menu.get()]
            values = (customer_id, name, species, fields["breed"].get(), gender_menu.get(),
                      fields["date_of_birth"].get(), weight, fields["special_notes"].get())
            if pet_id is None:
                add_pet(*values)
            else:
                update_pet(pet_id, *values)
        except sqlite3.IntegrityError:
            error_label.configure(text="Could not save this pet. Check the details and try again.")
            return
        window.destroy()
        self.load_pets()
        self.show_message("Pet updated successfully." if pet_id is not None else
                          "Pet added successfully.")

    def confirm_delete(self, pet_id):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Delete Pet")
        dialog.geometry("420x230")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["background"])
        ctk.CTkLabel(dialog, text="Delete this pet?\nPets with appointments cannot be deleted.",
                     font=("Arial", 14), text_color=COLORS["text"]).pack(pady=(30, 15))
        error_label = ctk.CTkLabel(dialog, text="", text_color=COLORS["error"], wraplength=370)
        error_label.pack(pady=5)
        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(pady=10)
        ctk.CTkButton(buttons, text="Cancel", fg_color=COLORS["blue"],
                      hover_color=COLORS["blue_hover"], command=dialog.destroy).pack(side="left", padx=5)
        ctk.CTkButton(buttons, text="Delete", fg_color=COLORS["pink"],
                      hover_color=COLORS["pink_hover"], text_color=COLORS["text"],
                      command=lambda: self.delete_pet_record(pet_id, dialog, error_label)).pack(side="left", padx=5)

    def delete_pet_record(self, pet_id, dialog, error_label):
        try:
            delete_pet(pet_id)
        except sqlite3.IntegrityError:
            error_label.configure(text="This pet has appointments and cannot be deleted.")
            return
        dialog.destroy()
        self.load_pets()
        self.show_message("Pet deleted successfully.")

    def show_message(self, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Pets")
        dialog.geometry("380x170")
        dialog.transient(self.winfo_toplevel())
        dialog.configure(fg_color=COLORS["background"])
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=message, text_color=COLORS["text"],
                     wraplength=330).pack(pady=30)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy,
                      fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"]).pack()
