import sqlite3
from pathlib import Path


# Get the main project folder.
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the location of the SQLite database file.
DATABASE_PATH = BASE_DIR / "pawfect_care.db"


def get_connection():
    """Create and return a connection to the Pawfect Care database."""

    connection = sqlite3.connect(DATABASE_PATH)

    # Enable foreign key enforcement in SQLite.
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection

if __name__ == "__main__":
    connection = get_connection()

    print("Database connection successful!")

    connection.close()