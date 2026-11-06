"""Securely create the first Admin account for a fresh installation."""

from getpass import getpass

from database.connection import get_connection
from utils.password import hash_password

MIN_PASSWORD_LENGTH = 12


def create_initial_admin(username, full_name, password):
    """Create the first Admin only while the users table is empty."""
    username = username.strip()
    full_name = full_name.strip()
    if len(username) < 3 or any(character.isspace() for character in username):
        raise ValueError("Username must be at least 3 characters and contain no spaces.")
    if not full_name:
        raise ValueError("Full name is required.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE;")
        count = connection.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
        if count:
            raise ValueError(
                "User accounts already exist. Create or manage accounts from User Management."
            )
        connection.execute("""
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, 'Admin');
        """, (username, hash_password(password), full_name))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main():
    print("Pawfect Care first Admin setup")
    print("The password will not be displayed while you type it.\n")
    username = input("Admin username: ").strip()
    full_name = input("Admin full name: ").strip()
    password = getpass("Admin password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        print("Setup cancelled: passwords do not match.")
        return 1
    try:
        create_initial_admin(username, full_name, password)
    except ValueError as error:
        print(f"Setup failed: {error}")
        return 1
    except Exception as error:
        if "no such table: users" in str(error).lower():
            print("Setup failed: create the database tables first with database/schema.py.")
        else:
            print(f"Setup failed: {error}")
        return 1
    print(f"Admin account '{username}' created. You can now launch Pawfect Care.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
