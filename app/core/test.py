from app.core.database import get_connection, init_db
import json

def test_db():
    # Initialize DB tables
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    # Insert sample variable
    cursor.execute("""
        INSERT INTO variable_names (variable_name, module, data_type, data_size, unit, description_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "AtddrvCTst1",
        "Analog to Digital Driver <Atddrv>",
        "CAN signals <C>",
        "Array/vector <a>",
        "Ampere <A>",
        json.dumps({"test1": "Tst1"})
    ))
    variable_id = cursor.lastrowid

    # Insert sample abbreviation
    cursor.execute("""
        INSERT INTO abbreviations (word, abbreviation, variable_id)
        VALUES (?, ?, ?)
    """, ("test1", "Tst1", variable_id))

    conn.commit()

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in DB:")
    for table in tables:
        print(table["name"])

    # Show all variable names
    cursor.execute("SELECT id, variable_name FROM variable_names;")
    vars = cursor.fetchall()
    print("\nVariable Names:")
    for v in vars:
        print(v["id"], v["variable_name"])

    # Show all abbreviations
    cursor.execute("SELECT id, word, abbreviation, variable_id FROM abbreviations;")
    abbrs = cursor.fetchall()
    print("\nAbbreviations:")
    for a in abbrs:
        print(a["id"], a["word"], a["abbreviation"], a["variable_id"])

    conn.close()


if __name__ == "__main__":
    test_db()
