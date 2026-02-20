import sqlite3
import os

# Path to database file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "app.db")


def get_connection():
    """
    Creates and returns a SQLite connection.
    Enables foreign key support.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows dict-like access
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    Creates database tables if they do not exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Create variable_names table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variable_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variable_name TEXT,
            module TEXT,
            data_type TEXT,
            data_size TEXT,
            unit TEXT,
            description_user TEXT,
            description_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create abbreviations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS abbreviations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT,
            abbreviation TEXT,
            variable_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (variable_id) REFERENCES variable_names(id)
        );
    """)

    conn.commit()
    conn.close()
