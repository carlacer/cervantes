"""Database operations for grooming services."""

from database.connection import get_connection


def get_all_services():
    """Return services with their category names."""
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT s.service_id, s.category_id, c.category_name,
                   s.service_name, s.description, s.price,
                   s.duration_minutes, s.is_active
            FROM services AS s
            JOIN service_categories AS c ON c.category_id = s.category_id
            ORDER BY c.category_name, s.service_name;
        """).fetchall()
    finally:
        connection.close()


def get_all_categories():
    """Return available service categories as (id, name) pairs."""
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT category_id, category_name
            FROM service_categories
            ORDER BY category_name;
        """).fetchall()
    finally:
        connection.close()


def add_service(category_id, service_name, description, price, duration_minutes):
    """Create a service and return its database ID."""
    connection = get_connection()
    try:
        cursor = connection.execute("""
            INSERT INTO services (category_id, service_name, description,
                                  price, duration_minutes)
            VALUES (?, ?, ?, ?, ?);
        """, (category_id, service_name.strip(), _optional(description),
              price, duration_minutes))
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_service(service_id, category_id, service_name, description,
                   price, duration_minutes, is_active):
    """Update a service's details and availability."""
    connection = get_connection()
    try:
        connection.execute("""
            UPDATE services
            SET category_id = ?, service_name = ?, description = ?,
                price = ?, duration_minutes = ?, is_active = ?
            WHERE service_id = ?;
        """, (category_id, service_name.strip(), _optional(description),
              price, duration_minutes, int(bool(is_active)), service_id))
        connection.commit()
    finally:
        connection.close()


def delete_service(service_id):
    """Delete a service. Raises IntegrityError if appointments use it."""
    connection = get_connection()
    try:
        connection.execute("DELETE FROM services WHERE service_id = ?;", (service_id,))
        connection.commit()
    finally:
        connection.close()


def _optional(value):
    value = value.strip() if value else ""
    return value or None
