import sqlite3
from app.core.database import get_connection, init_db
init_db()

class DatabaseService:
    @staticmethod
    def insert_variable_name(
        
        variable_name: str,
        module: str = None,
        data_type: str = None,
        data_size: str = None,
        unit: str = None,
        description_user: str = None,
        description_json: dict = None,
    ) -> int:
        """
        Inserts a variable name record into the DB.
        Returns the inserted row ID.
        """
        init_db()  # Ensure DB is initialized before any operation
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO variable_names
            (variable_name, module, data_type, data_size, unit, description_user, description_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            variable_name,
            module,
            data_type,
            data_size,
            unit,
            description_user,
            str(description_json) if description_json else None
        ))

        conn.commit()
        variable_id = cursor.lastrowid
        conn.close()
        return variable_id

    @staticmethod
    def insert_abbreviation(word: str, abbreviation: str, variable_id: int):
        """
        Insert a word abbreviation linked to a variable.
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO abbreviations (word, abbreviation, variable_id)
            VALUES (?, ?, ?)
        """, (word, abbreviation, variable_id))

        conn.commit()
        conn.close()

    @staticmethod
    def get_words_by_abbreviation(abbreviation: str):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT word FROM abbreviations WHERE LOWER(abbreviation) = LOWER(?)",
            (abbreviation,)
        )

        records = cursor.fetchall()
        conn.close()

        return [row[0] for row in records]

        