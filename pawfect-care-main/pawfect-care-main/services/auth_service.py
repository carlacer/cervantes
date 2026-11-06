from database.connection import get_connection
from utils.password import verify_password


class AccountDeactivatedError(Exception):
    """Raised when valid credentials belong to an inactive account."""


def authenticate_user(username, password):
    """Authenticate a user using their username and password."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                user_id,
                username,
                password_hash,
                full_name,
                role,
                is_active
            FROM users
            WHERE username = ?;
        """, (username,))

        user = cursor.fetchone()

        # Username does not exist.
        if user is None:
            return None

        user_id, username, password_hash, full_name, role, is_active = user

        # Password is incorrect.
        if not verify_password(password, password_hash):
            return None

        # Only reveal account status after the password is verified.
        if is_active != 1:
            raise AccountDeactivatedError(
                "Your account may be deactivated. Please contact an administrator."
            )

        # Authentication successful.
        return {
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "role": role,
        }

    finally:
        connection.close()
