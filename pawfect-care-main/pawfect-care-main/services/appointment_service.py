"""Database operations and lifecycle rules for appointments."""

import uuid
from datetime import datetime

from database.connection import get_connection

STATUS_TRANSITIONS = {
    "Pending": {"Confirmed", "Cancelled"},
    "Confirmed": {"In Progress", "Cancelled"},
    "In Progress": {"Completed"},
    "Completed": set(),
    "Cancelled": set(),
}


class AppointmentRuleError(ValueError):
    """Raised when an appointment action violates its lifecycle rules."""


def get_all_appointments():
    """Return appointment rows with customer, pet, services, and payment state."""
    connection = get_connection()
    try:
        _ensure_appointment_type_column(connection)
        return connection.execute("""
            SELECT a.appointment_id, a.appointment_number, a.pet_id,
                   p.pet_name, p.customer_id,
                   c.first_name || ' ' || c.last_name AS customer_name,
                   a.appointment_date, a.appointment_time, a.status, a.notes,
                   COALESCE(GROUP_CONCAT(s.service_name, ', '), '') AS service_names,
                   COALESCE(SUM(aps.service_price), 0) AS total,
                   EXISTS(SELECT 1 FROM payments pay
                          WHERE pay.appointment_id = a.appointment_id) AS has_payment
                   , a.appointment_type
                   , a.groomer_id, COALESCE(g.full_name, '') AS groomer_name
            FROM appointments a
            JOIN pets p ON p.pet_id = a.pet_id
            JOIN customers c ON c.customer_id = p.customer_id
            LEFT JOIN users g ON g.user_id = a.groomer_id
            LEFT JOIN appointment_services aps ON aps.appointment_id = a.appointment_id
            LEFT JOIN services s ON s.service_id = aps.service_id
            GROUP BY a.appointment_id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC,
                     a.appointment_id DESC;
        """).fetchall()
    finally:
        connection.close()


def get_customer_pets(customer_id):
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT pet_id, pet_name, species
            FROM pets WHERE customer_id = ?
            ORDER BY pet_name;
        """, (customer_id,)).fetchall()
    finally:
        connection.close()


def get_active_groomers():
    """Return active Groomer accounts that can be assigned to appointments."""
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT user_id, full_name
            FROM users WHERE role = 'Groomer' AND is_active = 1
            ORDER BY full_name COLLATE NOCASE;
        """).fetchall()
    finally:
        connection.close()


def get_active_services():
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT service_id, service_name, price, duration_minutes
            FROM services WHERE is_active = 1
            ORDER BY service_name;
        """).fetchall()
    finally:
        connection.close()


def get_services_for_appointment(appointment_id=None):
    """Return active services plus inactive services already on an appointment."""
    connection = get_connection()
    try:
        if appointment_id is None:
            query = "SELECT service_id, service_name, price, duration_minutes FROM services WHERE is_active = 1 ORDER BY service_name;"
            return connection.execute(query).fetchall()
        return connection.execute("""
            SELECT s.service_id, s.service_name, s.price, s.duration_minutes
            FROM services s
            WHERE s.is_active = 1 OR s.service_id IN (
                SELECT service_id FROM appointment_services WHERE appointment_id = ?
            )
            ORDER BY s.service_name;
        """, (appointment_id,)).fetchall()
    finally:
        connection.close()


def get_appointment_service_ids(appointment_id):
    connection = get_connection()
    try:
        return [row[0] for row in connection.execute("""
            SELECT service_id FROM appointment_services
            WHERE appointment_id = ? ORDER BY service_id;
        """, (appointment_id,)).fetchall()]
    finally:
        connection.close()


def create_appointment(pet_id, appointment_date, appointment_time, notes,
                       service_ids, groomer_id=None):
    """Create an appointment and snapshot selected service prices atomically."""
    service_ids = _normalized_service_ids(service_ids)
    if not service_ids:
        raise AppointmentRuleError("Select at least one service.")
    appointment_date, appointment_time = _validate_appointment_datetime(
        appointment_date, appointment_time
    )
    connection = get_connection()
    try:
        _ensure_appointment_type_column(connection)
        cursor = connection.cursor()
        _validate_no_duplicate(cursor, pet_id, appointment_date, appointment_time)
        groomer_id = _validate_groomer(cursor, groomer_id)
        number = "PC-" + uuid.uuid4().hex[:10].upper()
        cursor.execute("""
            INSERT INTO appointments (appointment_number, pet_id, groomer_id, appointment_date,
                                     appointment_time, notes, appointment_type)
            VALUES (?, ?, ?, ?, ?, ?, 'Appointment');
        """, (number, pet_id, groomer_id, appointment_date, appointment_time,
              _optional(notes)))
        appointment_id = cursor.lastrowid
        _replace_services(cursor, appointment_id, service_ids)
        connection.commit()
        return appointment_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def register_walk_in_visit(pet_id, notes, service_ids, groomer_id=None):
    """Register a walk-in as a visit that starts in progress now."""
    service_ids = _normalized_service_ids(service_ids)
    if not service_ids:
        raise AppointmentRuleError("Select at least one service.")
    now = datetime.now()
    appointment_date = now.date().isoformat()
    appointment_time = now.strftime("%H:%M")
    connection = get_connection()
    try:
        _ensure_appointment_type_column(connection)
        cursor = connection.cursor()
        _validate_no_duplicate(cursor, pet_id, appointment_date, appointment_time)
        groomer_id = _validate_groomer(cursor, groomer_id)
        number = "PC-" + uuid.uuid4().hex[:10].upper()
        cursor.execute("""
            INSERT INTO appointments (appointment_number, pet_id, groomer_id, appointment_date,
                appointment_time, status, notes, appointment_type)
            VALUES (?, ?, ?, ?, ?, 'In Progress', ?, 'Walk-in Visit');
        """, (number, pet_id, groomer_id, appointment_date, appointment_time,
              _optional(notes)))
        appointment_id = cursor.lastrowid
        _replace_services(cursor, appointment_id, service_ids)
        connection.commit()
        return appointment_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_appointment(appointment_id, pet_id, appointment_date, appointment_time,
                       notes, service_ids, groomer_id=None):
    """Update appointment details and selected services atomically."""
    service_ids = _normalized_service_ids(service_ids)
    if not service_ids:
        raise AppointmentRuleError("Select at least one service.")
    appointment_date, appointment_time = _validate_appointment_datetime(
        appointment_date, appointment_time
    )
    connection = get_connection()
    try:
        _ensure_appointment_type_column(connection)
        cursor = connection.cursor()
        status = _get_status(cursor, appointment_id)
        if status not in ("Pending", "Confirmed"):
            raise AppointmentRuleError(f"A {status.lower()} appointment cannot be edited.")
        _validate_no_duplicate(cursor, pet_id, appointment_date, appointment_time, appointment_id)
        groomer_id = _validate_groomer(cursor, groomer_id, appointment_id)
        cursor.execute("""
            UPDATE appointments
            SET pet_id = ?, groomer_id = ?, appointment_date = ?, appointment_time = ?, notes = ?
            WHERE appointment_id = ?;
        """, (pet_id, groomer_id, appointment_date, appointment_time,
              _optional(notes), appointment_id))
        _replace_services(cursor, appointment_id, service_ids)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_appointment_status(appointment_id, new_status):
    """Apply only valid forward status transitions."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        current = _get_status(cursor, appointment_id)
        if new_status not in STATUS_TRANSITIONS.get(current, set()):
            raise AppointmentRuleError(
                f"Cannot change status from {current} to {new_status}."
            )
        cursor.execute("UPDATE appointments SET status = ? WHERE appointment_id = ?;",
                       (new_status, appointment_id))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def cancel_appointment(appointment_id):
    """Cancel only pending or confirmed appointments."""
    update_appointment_status(appointment_id, "Cancelled")


def delete_appointment(appointment_id):
    """Delete only cancelled appointments that have no payment record."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        status = _get_status(cursor, appointment_id)
        if status != "Cancelled":
            raise AppointmentRuleError("Only cancelled appointments can be deleted.")
        payment = cursor.execute(
            "SELECT 1 FROM payments WHERE appointment_id = ?;", (appointment_id,)
        ).fetchone()
        if payment:
            raise AppointmentRuleError("An appointment with a payment cannot be deleted.")
        cursor.execute("DELETE FROM appointment_services WHERE appointment_id = ?;",
                       (appointment_id,))
        cursor.execute("DELETE FROM appointments WHERE appointment_id = ?;",
                       (appointment_id,))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _get_status(cursor, appointment_id):
    row = cursor.execute("SELECT status FROM appointments WHERE appointment_id = ?;",
                         (appointment_id,)).fetchone()
    if row is None:
        raise AppointmentRuleError("Appointment was not found.")
    return row[0]


def _validate_groomer(cursor, groomer_id, appointment_id=None):
    """Return a valid groomer id (or None for unassigned)."""
    if groomer_id is None:
        return None
    row = cursor.execute(
        "SELECT is_active FROM users WHERE user_id = ? AND role = 'Groomer';",
        (groomer_id,),
    ).fetchone()
    if row is None:
        raise AppointmentRuleError("Selected groomer was not found.")
    if row[0] != 1:
        # Keep an already-assigned groomer even if they were deactivated later.
        current = None
        if appointment_id is not None:
            current = cursor.execute(
                "SELECT groomer_id FROM appointments WHERE appointment_id = ?;",
                (appointment_id,),
            ).fetchone()
        if not current or current[0] != groomer_id:
            raise AppointmentRuleError("Selected groomer account is deactivated.")
    return groomer_id


def _ensure_appointment_type_column(connection):
    columns = {row[1] for row in connection.execute("PRAGMA table_info(appointments);").fetchall()}
    if "appointment_type" not in columns:
        connection.execute("""
            ALTER TABLE appointments
            ADD COLUMN appointment_type TEXT NOT NULL DEFAULT 'Appointment'
                CHECK (appointment_type IN ('Appointment', 'Walk-in Visit'));
        """)
        connection.commit()


def _validate_appointment_datetime(appointment_date, appointment_time):
    try:
        parsed = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
    except (TypeError, ValueError) as error:
        raise AppointmentRuleError("Enter a valid date (YYYY-MM-DD) and time (HH:MM).") from error
    if parsed < datetime.now():
        raise AppointmentRuleError("Appointments cannot be scheduled in the past.")
    return parsed.date().isoformat(), parsed.strftime("%H:%M")


def _validate_no_duplicate(cursor, pet_id, appointment_date, appointment_time,
                           exclude_appointment_id=None):
    query = """
        SELECT appointment_number FROM appointments
        WHERE pet_id = ? AND appointment_date = ? AND appointment_time = ?
          AND status != 'Cancelled'
    """
    parameters = [pet_id, appointment_date, appointment_time]
    if exclude_appointment_id is not None:
        query += " AND appointment_id != ?"
        parameters.append(exclude_appointment_id)
    if cursor.execute(query, parameters).fetchone():
        raise AppointmentRuleError(
            "This pet already has an active appointment at that date and time."
        )


def _replace_services(cursor, appointment_id, service_ids):
    placeholders = ",".join("?" for _ in service_ids)
    previous_prices = dict(cursor.execute(
        "SELECT service_id, service_price FROM appointment_services WHERE appointment_id = ?;",
        (appointment_id,),
    ).fetchall())
    services = cursor.execute(
        f"""SELECT service_id, price FROM services
            WHERE service_id IN ({placeholders}) AND (
                is_active = 1 OR service_id IN (
                    SELECT service_id FROM appointment_services WHERE appointment_id = ?
                )
            );""",
        [*service_ids, appointment_id],
    ).fetchall()
    prices = {service_id: price for service_id, price in services}
    if len(prices) != len(service_ids):
        raise AppointmentRuleError("One or more selected services are no longer available.")
    cursor.execute("DELETE FROM appointment_services WHERE appointment_id = ?;",
                   (appointment_id,))
    cursor.executemany("""
        INSERT INTO appointment_services (appointment_id, service_id, service_price)
        VALUES (?, ?, ?);
    """, [(appointment_id, service_id, previous_prices.get(service_id, prices[service_id]))
          for service_id in service_ids])


def _normalized_service_ids(service_ids):
    try:
        return sorted({int(service_id) for service_id in service_ids})
    except (TypeError, ValueError) as error:
        raise AppointmentRuleError("Invalid service selection.") from error


def _optional(value):
    value = value.strip() if value else ""
    return value or None