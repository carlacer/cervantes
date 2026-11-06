from database.connection import get_connection


def inspect_table(table_name):
    """Display the structure of a database table."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            f"PRAGMA table_info({table_name});"
        )

        columns = cursor.fetchall()

        print(f"\nTABLE: {table_name}")
        print("-" * 50)

        for column in columns:
            column_id = column[0]
            name = column[1]
            data_type = column[2]
            not_null = column[3]
            default_value = column[4]
            primary_key = column[5]

            print(
                f"{column_id}. "
                f"{name} | "
                f"{data_type} | "
                f"NOT NULL: {not_null} | "
                f"DEFAULT: {default_value} | "
                f"PRIMARY KEY: {primary_key}"
            )

    finally:
        connection.close()


if __name__ == "__main__":
    inspect_table("customers")