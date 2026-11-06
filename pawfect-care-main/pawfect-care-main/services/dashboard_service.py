"""Read-only queries used by the admin dashboard."""

from datetime import date

from database.connection import get_connection

APPOINTMENT_STATUSES = ("Pending", "Confirmed", "In Progress", "Completed", "Cancelled")


def get_dashboard_data():
    """Return live customer, pet, appointment, and today's schedule data."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        customer_count = cursor.execute("SELECT COUNT(*) FROM customers;").fetchone()[0]
        pet_count = cursor.execute("SELECT COUNT(*) FROM pets;").fetchone()[0]
        appointment_count = cursor.execute("SELECT COUNT(*) FROM appointments;").fetchone()[0]

        status_counts = {status: 0 for status in APPOINTMENT_STATUSES}
        status_counts.update(dict(cursor.execute("""
            SELECT status, COUNT(*)
            FROM appointments
            GROUP BY status;
        """).fetchall()))

        today_appointments = cursor.execute("""
            SELECT a.appointment_id, a.appointment_number,
                   a.appointment_time, a.status, p.pet_name,
                   c.first_name || ' ' || c.last_name AS customer_name,
                   COALESCE(GROUP_CONCAT(s.service_name, ', '), '') AS service_names
            FROM appointments a
            JOIN pets p ON p.pet_id = a.pet_id
            JOIN customers c ON c.customer_id = p.customer_id
            LEFT JOIN appointment_services aps ON aps.appointment_id = a.appointment_id
            LEFT JOIN services s ON s.service_id = aps.service_id
            WHERE a.appointment_date = ?
            GROUP BY a.appointment_id
            ORDER BY a.appointment_time, a.appointment_id;
        """, (date.today().isoformat(),)).fetchall()

        return {
            "customer_count": customer_count,
            "pet_count": pet_count,
            "appointment_count": appointment_count,
            "status_counts": status_counts,
            "today_appointments": today_appointments,
        }
    finally:
        connection.close()
