from app.core.database import get_connection, init_db
import json

def test_db():
    # Initialize DB tables
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in DB:")
    for table in tables:
        print(dict(table))  # full row

    # Show all variable_names rows (full row)
    cursor.execute("SELECT * FROM variable_names;")
    vars = cursor.fetchall()
    print("\nVariable Names:")
    for v in vars:
        print(dict(v))  # full row

    # Show all abbreviations rows (full row)
    cursor.execute("SELECT * FROM abbreviations;")
    abbrs = cursor.fetchall()
    print("\nAbbreviations:")
    for a in abbrs:
        print(dict(a))  # full row

    conn.close()


if __name__ == "__main__":
    test_db()