from database.connection import get_connection


def create_tables():
    """Create all Pawfect Care database tables."""

    connection = get_connection()
    cursor = connection.cursor()

    # 1. Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,

            role TEXT NOT NULL
                CHECK (role IN ('Admin', 'Groomer')),

            is_active INTEGER NOT NULL DEFAULT 1
                CHECK (is_active IN (0, 1)),

            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,

            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,

            contact_number TEXT NOT NULL,
            email TEXT,
            address TEXT,

            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Service Categories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,

            category_name TEXT NOT NULL UNIQUE,
            description TEXT
        );
    """)

    # 4. Pets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            pet_id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_id INTEGER NOT NULL,

            pet_name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT,

            gender TEXT
                CHECK (gender IN ('Male', 'Female', 'Unknown')),

            date_of_birth TEXT,

            weight REAL
                CHECK (weight IS NULL OR weight > 0),

            special_notes TEXT,

            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        );
    """)

    # 5. Services
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            service_id INTEGER PRIMARY KEY AUTOINCREMENT,

            category_id INTEGER NOT NULL,

            service_name TEXT NOT NULL,
            description TEXT,

            price REAL NOT NULL
                CHECK (price >= 0),

            duration_minutes INTEGER NOT NULL
                CHECK (duration_minutes > 0),

            is_active INTEGER NOT NULL DEFAULT 1
                CHECK (is_active IN (0, 1)),

            FOREIGN KEY (category_id)
                REFERENCES service_categories(category_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE,

            UNIQUE (category_id, service_name)
        );
    """)

    # 6. Appointments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,

            appointment_number TEXT NOT NULL UNIQUE,

            pet_id INTEGER NOT NULL,
            groomer_id INTEGER,

            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'Pending'
                CHECK (
                    status IN (
                        'Pending',
                        'Confirmed',
                        'In Progress',
                        'Completed',
                        'Cancelled'
                    )
                ),

            appointment_type TEXT NOT NULL DEFAULT 'Appointment'
                CHECK (appointment_type IN ('Appointment', 'Walk-in Visit')),

            notes TEXT,

            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (pet_id)
                REFERENCES pets(pet_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE,

            FOREIGN KEY (groomer_id)
                REFERENCES users(user_id)
                ON DELETE SET NULL
                ON UPDATE CASCADE
        );
    """)

    appointment_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(appointments);").fetchall()
    }
    if "appointment_type" not in appointment_columns:
        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN appointment_type TEXT NOT NULL DEFAULT 'Appointment'
                CHECK (appointment_type IN ('Appointment', 'Walk-in Visit'));
        """)

    # 7. Appointment Services
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointment_services (
            appointment_service_id INTEGER PRIMARY KEY AUTOINCREMENT,

            appointment_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,

            service_price REAL NOT NULL
                CHECK (service_price >= 0),

            FOREIGN KEY (appointment_id)
                REFERENCES appointments(appointment_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE,

            FOREIGN KEY (service_id)
                REFERENCES services(service_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE,

            UNIQUE (appointment_id, service_id)
        );
    """)

    # 8. Payments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,

            appointment_id INTEGER NOT NULL UNIQUE,

            total_amount REAL NOT NULL
                CHECK (total_amount >= 0),

            payment_method TEXT NOT NULL
                CHECK (
                    payment_method IN (
                        'Cash',
                        'GCash',
                        'Maya'
                    )
                ),

            status TEXT NOT NULL DEFAULT 'Paid'
                CHECK (status IN ('Pending', 'Paid', 'Refunded')),

            payment_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (appointment_id)
                REFERENCES appointments(appointment_id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        );
    """)

    # Add status to databases created before payment status tracking existed.
    payment_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(payments);").fetchall()
    }
    if "status" not in payment_columns:
        cursor.execute("""
            ALTER TABLE payments
            ADD COLUMN status TEXT NOT NULL DEFAULT 'Paid'
                CHECK (status IN ('Pending', 'Paid', 'Refunded'));
        """)

    connection.commit()
    connection.close()

    print("All database tables created successfully!")

def verify_tables():
    """Display all tables currently in the database."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name;
    """)

    tables = cursor.fetchall()

    print("\nTables in pawfect_care.db:")

    for table in tables:
        print(f"- {table[0]}")

    connection.close()

    
if __name__ == "__main__":
    create_tables()
    verify_tables()
