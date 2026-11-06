"""Database operations and business rules for payments."""

from database.connection import get_connection

PAYMENT_STATUSES = ("Pending", "Paid", "Refunded")
PAYMENT_TRANSITIONS = {
    "Pending": {"Paid"},
    "Paid": {"Refunded"},
    "Refunded": set(),
}
PAYMENT_METHODS = ("Cash", "GCash", "Maya")


class PaymentRuleError(ValueError):
    """Raised when a payment action violates its rules."""


def get_all_payments():
    connection = get_connection()
    try:
        _ensure_status_column(connection)
        return connection.execute("""
            SELECT pay.payment_id, pay.appointment_id, a.appointment_number,
                   c.first_name || ' ' || c.last_name AS customer_name,
                   p.pet_name, a.appointment_date, a.appointment_time,
                   pay.total_amount, pay.payment_method, pay.status, pay.payment_date
            FROM payments pay
            JOIN appointments a ON a.appointment_id = pay.appointment_id
            JOIN pets p ON p.pet_id = a.pet_id
            JOIN customers c ON c.customer_id = p.customer_id
            ORDER BY pay.payment_date DESC, pay.payment_id DESC;
        """).fetchall()
    finally:
        connection.close()


def get_payable_appointments():
    """Completed appointments without a payment, including their calculated total."""
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT a.appointment_id, a.appointment_number, a.appointment_date,
                   a.appointment_time, p.pet_name,
                   c.first_name || ' ' || c.last_name AS customer_name,
                   COALESCE(SUM(aps.service_price), 0) AS total,
                   COUNT(aps.appointment_service_id) AS service_count
            FROM appointments a
            JOIN pets p ON p.pet_id = a.pet_id
            JOIN customers c ON c.customer_id = p.customer_id
            LEFT JOIN appointment_services aps ON aps.appointment_id = a.appointment_id
            LEFT JOIN payments pay ON pay.appointment_id = a.appointment_id
            WHERE a.status = 'Completed' AND pay.payment_id IS NULL
            GROUP BY a.appointment_id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC;
        """).fetchall()
    finally:
        connection.close()


def calculate_appointment_total(appointment_id):
    connection = get_connection()
    try:
        row = connection.execute("""
            SELECT COALESCE(SUM(service_price), 0)
            FROM appointment_services WHERE appointment_id = ?;
        """, (appointment_id,)).fetchone()
        return row[0]
    finally:
        connection.close()


def record_payment(appointment_id, payment_method, status="Paid"):
    """Record a payment using the appointment's captured service prices."""
    if payment_method not in PAYMENT_METHODS:
        raise PaymentRuleError("Select a valid payment method.")
    if status not in ("Pending", "Paid"):
        raise PaymentRuleError("New payments must be Pending or Paid.")
    connection = get_connection()
    try:
        _ensure_status_column(connection)
        cursor = connection.cursor()
        appointment = cursor.execute(
            "SELECT status FROM appointments WHERE appointment_id = ?;",
            (appointment_id,),
        ).fetchone()
        if appointment is None:
            raise PaymentRuleError("Appointment was not found.")
        if appointment[0] != "Completed":
            raise PaymentRuleError("Payment can only be recorded for a completed appointment.")
        if cursor.execute("SELECT 1 FROM payments WHERE appointment_id = ?;",
                          (appointment_id,)).fetchone():
            raise PaymentRuleError("This appointment already has a payment record.")
        total = cursor.execute("""
            SELECT COALESCE(SUM(service_price), 0)
            FROM appointment_services WHERE appointment_id = ?;
        """, (appointment_id,)).fetchone()[0]
        service_count = cursor.execute(
            "SELECT COUNT(*) FROM appointment_services WHERE appointment_id = ?;",
            (appointment_id,),
        ).fetchone()[0]
        if not service_count:
            raise PaymentRuleError("This appointment has no services to charge.")
        cursor.execute("""
            INSERT INTO payments (appointment_id, total_amount, payment_method, status)
            VALUES (?, ?, ?, ?);
        """, (appointment_id, total, payment_method, status))
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_payment_status(payment_id, new_status):
    connection = get_connection()
    try:
        _ensure_status_column(connection)
        cursor = connection.cursor()
        row = cursor.execute("SELECT status FROM payments WHERE payment_id = ?;",
                             (payment_id,)).fetchone()
        if row is None:
            raise PaymentRuleError("Payment was not found.")
        current = row[0]
        if new_status not in PAYMENT_TRANSITIONS.get(current, set()):
            raise PaymentRuleError(f"Cannot change payment status from {current} to {new_status}.")
        cursor.execute("UPDATE payments SET status = ? WHERE payment_id = ?;",
                       (new_status, payment_id))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _ensure_status_column(connection):
    columns = {row[1] for row in connection.execute("PRAGMA table_info(payments);").fetchall()}
    if "status" not in columns:
        connection.execute("""
            ALTER TABLE payments
            ADD COLUMN status TEXT NOT NULL DEFAULT 'Paid'
                CHECK (status IN ('Pending', 'Paid', 'Refunded'));
        """)
        connection.commit()
