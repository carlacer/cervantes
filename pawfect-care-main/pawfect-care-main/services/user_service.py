"""User account management and role safeguards."""

from database.connection import get_connection
from utils.password import hash_password

USER_ROLES = ("Admin", "Groomer")


class UserRuleError(ValueError):
    """Raised when a requested user change would create an invalid account state."""


def get_all_users():
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT user_id, username, full_name, role, is_active, created_at
            FROM users ORDER BY full_name COLLATE NOCASE, username COLLATE NOCASE;
        """).fetchall()
    finally:
        connection.close()


def add_user(username, full_name, role, password):
    username, full_name = _validate_identity(username, full_name, role)
    _validate_password(password)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if cursor.execute("SELECT 1 FROM users WHERE lower(username) = lower(?);",
                          (username,)).fetchone():
            raise UserRuleError("That username is already in use.")
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?);
        """, (username, hash_password(password), full_name, role))
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_user(user_id, username, full_name, role, acting_user_id=None):
    username, full_name = _validate_identity(username, full_name, role)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        current = cursor.execute("SELECT role FROM users WHERE user_id = ?;", (user_id,)).fetchone()
        if current is None:
            raise UserRuleError("User was not found.")
        if cursor.execute("""
            SELECT 1 FROM users WHERE lower(username) = lower(?) AND user_id != ?;
        """, (username, user_id)).fetchone():
            raise UserRuleError("That username is already in use.")
        if user_id == acting_user_id and role != current[0]:
            raise UserRuleError("You cannot change your own role while signed in.")
        if current[0] == "Admin" and role != "Admin":
            active = cursor.execute("SELECT is_active FROM users WHERE user_id = ?;",
                                    (user_id,)).fetchone()[0]
            if active:
                _require_another_active_admin(cursor, user_id)
        cursor.execute("""
            UPDATE users SET username = ?, full_name = ?, role = ?
            WHERE user_id = ?;
        """, (username, full_name, role, user_id))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def reset_user_password(user_id, password):
    _validate_password(password)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if not cursor.execute("SELECT 1 FROM users WHERE user_id = ?;", (user_id,)).fetchone():
            raise UserRuleError("User was not found.")
        cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?;",
                       (hash_password(password), user_id))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def set_user_active(user_id, is_active, acting_user_id=None):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        user = cursor.execute("SELECT role, is_active FROM users WHERE user_id = ?;",
                              (user_id,)).fetchone()
        if user is None:
            raise UserRuleError("User was not found.")
        role, current_active = user
        is_active = bool(is_active)
        if not is_active and user_id == acting_user_id:
            raise UserRuleError("You cannot deactivate your own account.")
        if not is_active and role == "Admin" and current_active:
            _require_another_active_admin(cursor, user_id)
        cursor.execute("UPDATE users SET is_active = ? WHERE user_id = ?;",
                       (int(is_active), user_id))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _require_another_active_admin(cursor, user_id):
    count = cursor.execute("""
        SELECT COUNT(*) FROM users
        WHERE role = 'Admin' AND is_active = 1 AND user_id != ?;
    """, (user_id,)).fetchone()[0]
    if count == 0:
        raise UserRuleError("The system must keep at least one active Admin account.")


def _validate_identity(username, full_name, role):
    username = username.strip() if username else ""
    full_name = full_name.strip() if full_name else ""
    if not username or not full_name:
        raise UserRuleError("Username and full name are required.")
    if len(username) < 3 or any(character.isspace() for character in username):
        raise UserRuleError("Username must be at least 3 characters and contain no spaces.")
    if role not in USER_ROLES:
        raise UserRuleError("Choose Admin or Groomer as the role.")
    return username, full_name


def _validate_password(password):
    if not password or len(password) < 12:
        raise UserRuleError("Password must be at least 12 characters long.")
