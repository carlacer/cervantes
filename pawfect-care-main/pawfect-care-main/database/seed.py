from database.connection import get_connection


def seed_categories(cursor):
    """Insert the default service categories."""

    categories = [
        (
            "Bath & Grooming",
            "Bathing, grooming, haircut, and coat care services."
        ),
        (
            "Cleaning & Hygiene",
            "Cleaning and hygiene maintenance services."
        ),
        (
            "Special Treatments",
            "Special grooming and treatment services."
        ),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO service_categories (
            category_name,
            description
        )
        VALUES (?, ?);
    """, categories)


def get_category_id(cursor, category_name):
    """Get the ID of a service category by its name."""

    cursor.execute("""
        SELECT category_id
        FROM service_categories
        WHERE category_name = ?;
    """, (category_name,))

    result = cursor.fetchone()

    return result[0]


def seed_services(cursor):
    """Insert the default grooming services."""

    services = [
        # Bath & Grooming
        ("Bath & Grooming", "Basic Bath", 250.00, 30),
        ("Bath & Grooming", "Full Grooming", 500.00, 90),
        ("Bath & Grooming", "Haircut / Trimming", 300.00, 45),
        ("Bath & Grooming", "De-shedding", 350.00, 45),

        # Cleaning & Hygiene
        ("Cleaning & Hygiene", "Nail Clipping", 100.00, 15),
        ("Cleaning & Hygiene", "Ear Cleaning", 100.00, 15),
        ("Cleaning & Hygiene", "Teeth Cleaning", 150.00, 20),
        ("Cleaning & Hygiene", "Paw Pad Trimming", 100.00, 15),

        # Special Treatments
        ("Special Treatments", "Flea & Tick Treatment", 300.00, 30),
        ("Special Treatments", "Anal Gland Cleaning", 200.00, 20),
    ]

    for category_name, service_name, price, duration in services:

        category_id = get_category_id(
            cursor,
            category_name
        )

        cursor.execute("""
            INSERT OR IGNORE INTO services (
                category_id,
                service_name,
                price,
                duration_minutes
            )
            VALUES (?, ?, ?, ?);
        """, (
            category_id,
            service_name,
            price,
            duration
        ))


def seed_database():
    """Insert non-sensitive catalog data. Admin accounts are set up separately."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        seed_categories(cursor)
        seed_services(cursor)

        connection.commit()

        print("Database seeded successfully!")

    except Exception as error:
        connection.rollback()

        print(f"Error seeding database: {error}")

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    seed_database()
