from database.connection import get_connection


class CustomerRuleError(ValueError):
    """Raised when customer data conflicts with an existing record."""


def get_all_customers():
    """Get all customers from the database."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                customer_id,
                first_name,
                last_name,
                contact_number,
                email,
                address,
                created_at
            FROM customers
            ORDER BY customer_id DESC;
        """)

        return cursor.fetchall()

    finally:
        connection.close()


def add_customer(
    first_name,
    last_name,
    contact_number,
    email,
    address
):
    """Add a new customer to the database."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        _validate_unique_customer(cursor, contact_number, email)
        cursor.execute("""
            INSERT INTO customers (
                first_name,
                last_name,
                contact_number,
                email,
                address
            )
            VALUES (?, ?, ?, ?, ?);
        """, (
            first_name.strip(),
            last_name.strip(),
            contact_number.strip(),
            email.strip() if email else None,
            address.strip() if address else None
        ))

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_customer_by_id(customer_id):
    """Get one customer using their ID."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                customer_id,
                first_name,
                last_name,
                contact_number,
                email,
                address,
                created_at
            FROM customers
            WHERE customer_id = ?;
        """, (customer_id,))

        return cursor.fetchone()

    finally:
        connection.close()


def update_customer(
    customer_id,
    first_name,
    last_name,
    contact_number,
    email,
    address
):
    """Update an existing customer."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        _validate_unique_customer(cursor, contact_number, email, customer_id)
        cursor.execute("""
            UPDATE customers
            SET
                first_name = ?,
                last_name = ?,
                contact_number = ?,
                email = ?,
                address = ?
            WHERE customer_id = ?;
        """, (
            first_name.strip(),
            last_name.strip(),
            contact_number.strip(),
            email.strip() if email else None,
            address.strip() if address else None,
            customer_id
        ))

        connection.commit()

    finally:
        connection.close()


def delete_customer(customer_id):
    """Delete a customer from the database."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            DELETE FROM customers
            WHERE customer_id = ?;
        """, (customer_id,))

        connection.commit()

    finally:
        connection.close()


def _validate_unique_customer(cursor, contact_number, email, exclude_customer_id=None):
    rows = cursor.execute("""
        SELECT customer_id, contact_number, email
        FROM customers;
    """).fetchall()
    phone_digits = "".join(character for character in contact_number if character.isdigit())
    for customer_id, existing_phone, existing_email in rows:
        if customer_id == exclude_customer_id:
            continue
        existing_digits = "".join(character for character in existing_phone if character.isdigit())
        if phone_digits and phone_digits == existing_digits:
            raise CustomerRuleError("A customer with this contact number already exists.")
        if email and existing_email and email.strip().casefold() == existing_email.strip().casefold():
            raise CustomerRuleError("A customer with this email address already exists.")
