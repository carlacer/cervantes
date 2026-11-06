"""Database operations for pet records."""

from database.connection import get_connection


def get_all_pets():
    """Return pets with their current owner's name."""
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT p.pet_id, p.customer_id, p.pet_name, p.species, p.breed,
                   p.gender, p.date_of_birth, p.weight, p.special_notes,
                   c.first_name, c.last_name
            FROM pets AS p
            JOIN customers AS c ON c.customer_id = p.customer_id
            ORDER BY p.pet_id DESC;
        """).fetchall()
    finally:
        connection.close()


def add_pet(customer_id, pet_name, species, breed=None, gender="Unknown",
            date_of_birth=None, weight=None, special_notes=None):
    """Add a pet and return its database ID."""
    connection = get_connection()
    try:
        cursor = connection.execute("""
            INSERT INTO pets (customer_id, pet_name, species, breed, gender,
                              date_of_birth, weight, special_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (customer_id, pet_name.strip(), species.strip(), _optional(breed),
              gender, _optional(date_of_birth), weight, _optional(special_notes)))
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_pet(pet_id, customer_id, pet_name, species, breed=None,
               gender="Unknown", date_of_birth=None, weight=None,
               special_notes=None):
    """Update a pet, including its assigned customer."""
    connection = get_connection()
    try:
        connection.execute("""
            UPDATE pets
            SET customer_id = ?, pet_name = ?, species = ?, breed = ?,
                gender = ?, date_of_birth = ?, weight = ?, special_notes = ?
            WHERE pet_id = ?;
        """, (customer_id, pet_name.strip(), species.strip(), _optional(breed),
              gender, _optional(date_of_birth), weight, _optional(special_notes),
              pet_id))
        connection.commit()
    finally:
        connection.close()


def delete_pet(pet_id):
    """Delete a pet. Raises sqlite3.IntegrityError if it has appointments."""
    connection = get_connection()
    try:
        connection.execute("DELETE FROM pets WHERE pet_id = ?;", (pet_id,))
        connection.commit()
    finally:
        connection.close()


def _optional(value):
    value = value.strip() if value else ""
    return value or None
