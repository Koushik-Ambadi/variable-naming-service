import os
from app.services.database_service import DatabaseService
from app.core.database import get_connection, init_db

# Initialize DB and tables (in case they don't exist)
init_db()

def test_insert_variable():
    # Sample data
    variable_data = {
        "variable_name": "Finance_int_USD_avgRevenue",
        "module": "Finance",
        "data_type": "int",
        "data_size": "4",
        "unit": "USD",
        "description_user": "Average Revenue",
        "description_json": {"Average": "avg", "Revenue": "rev"}
    }

    print("Inserting variable name into DB...")
    variable_id = DatabaseService.insert_variable_name(**variable_data)
    print(f"Inserted variable_name ID: {variable_id}")

    # Insert abbreviations
    for word, abbr in variable_data["description_json"].items():
        DatabaseService.insert_abbreviation(word, abbr, variable_id)
        print(f"Inserted abbreviation: {word} -> {abbr}")

    # Fetch inserted variable
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM variable_names WHERE id = ?", (variable_id,))
    var_row = cursor.fetchone()
    print("\nVariable row from DB:")
    print(dict(var_row))

    cursor.execute("SELECT * FROM abbreviations WHERE variable_id = ?", (variable_id,))
    abbr_rows = cursor.fetchall()
    print("\nAbbreviations linked to variable:")
    for row in abbr_rows:
        print(dict(row))

    conn.close()

def clear_all_data():
    """Delete all rows from variable_names and abbreviations tables."""
    conn = get_connection()
    cursor = conn.cursor()

    print("Clearing all data from database...")

    # Delete child table first (FK safety)
    cursor.execute("DELETE FROM abbreviations;")
    cursor.execute("DELETE FROM variable_names;")

    conn.commit()
    conn.close()

    print("All rows deleted from both tables.")


if __name__ == "__main__":
    clear_all_data()  # Clear existing data before test