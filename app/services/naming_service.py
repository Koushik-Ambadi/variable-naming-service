# app/services/naming_service.py
import json
import re
import os
import sqlite3

from app.services.database_service import DatabaseService
from app.core.database import get_connection, init_db

# Initialize DB and tables (in case they don't exist)
init_db()

class NamingService:


    STOPWORDS = [
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "as", "at", "be", "because", "been", "being",
        "below", "between", "both", "but", "by", "do", "does", "doing", "down",
        "each", "few", "for", "from", "further", "had", "has", "have", "he", "her", "here",
        "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
        "it", "its", "itself", "let's", "me", "more", "most", "my", "myself",
        "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
        "our", "ours", "ourselves", "out", "over", "own", "same", "she",
        "should", "so", "some", "such", "than", "that", "the", "their", "theirs",
        "them", "themselves", "then", "there", "these", "they", "this", "those",
        "through", "to", "too", "until", "up", "very", "was", "we",
        "were", "what", "when", "where", "which", "while", "who", "whom", "why",
        "with", "would", "you", "your", "yours", "yourself", "yourselves",
        "used", "in", "of", "for", "with", "from", "to", "by", "on", "at", "as",
        "into", "over", "under", "between", "through", "via", "about", "per",
        "within", "without", "along", "across", "among", "behind", "against",
        "toward", "around", "near"
    ]

    def __init__(self, format: str = "abs", standard: str = "autosar"):
        self.format = format
        self.standard = standard
        self.root_path = os.getcwd()

        self.base_path = os.path.join(self.root_path, f"data/naming_conventions/{self.format}")
        self.standard_path = os.path.join(self.root_path, f"data/standards/{self.standard}")

        self.config = self._safe_load(os.path.join(self.base_path, "format.json"))
        self.fields = self.config.get("fields", [])
        self.template = self.config.get("template", "{description}")

        self.endpoint_counts_path = os.path.join(self.root_path, "data/endpoint_counts.json")



    # ---------------------------
    # Utility Helpers
    # ---------------------------

    def _safe_load(self, path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _safe_save(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)



    def generate(self, body: dict):
        result = self.gen_var_name(**body)
        self.update_endpoint_count(f"/generate-variable-name")
        return result


    def get_format_fields(self):
        response = {}
        for field in self.fields:
            options_file = os.path.join(self.base_path, f"{field}s.json")
            options_data = self._safe_load(options_file)
            if options_data:
                response[field] = {"type": "select", "options": list(options_data.keys())}
            else:
                response[field] = {"type": "string", "description": f"Enter {field}"}
        return {"format": self.format, "fields": response}


    def get_stats(self):
        return self._safe_load(self.endpoint_counts_path)

    # ---------------------------
    # Core Naming Logic
    # ---------------------------

    def _load_abbreviation(self):
        path = os.path.join(self.standard_path, "abbreviation.json")
        data = self._safe_load(path)
        return {k.lower(): v for k, v in data.items()}



    # ---------------------------
    # Endpoint Stats
    # ---------------------------

    def update_endpoint_count(self, endpoint: str):
        stats = self._safe_load(self.endpoint_counts_path)
        stats[endpoint] = stats.get(endpoint, 0) + 1
        self._safe_save(self.endpoint_counts_path, stats)


    # ---------------------------
    # New Method: Get options for each word (stopwords removed)
    # ---------------------------
    
    def get_options_for_description(self, description: str):
        if not description:
            return {"words_options": {}}

        abbreviations = self._load_abbreviation()
        tokens = description.split()
        words_options = {}
        new_abbreviations = {}

        for token in tokens:
            token_lower = token.lower()
            if token_lower in self.STOPWORDS:
                continue

            options = []

            # Option 1: Complete word itself
            options.append({
                "value": token.capitalize(),  # keeping capitalization
                "in_use": False,               # can mark as in use
                "conflict": False
            })

            # Option 2: JSON dictionary abbreviation (existing)
            if token_lower in abbreviations:
                options.append({
                    "value": abbreviations[token_lower],
                    "in_use": False,
                    "conflict": False
                })

            # Option 3: regex-based rule
            first = token_lower[0]
            rest = re.sub(r'[aeiou]', '', token_lower[1:])
            rest = re.sub(r'(.)\1+', r'\1', rest)
            abbr2 = (first + rest)[:6].capitalize()
            conflict2 = abbr2 in new_abbreviations.values() or abbr2 in abbreviations.values()
            options.append({
                "value": abbr2,
                "in_use": False,
                "conflict": False #All False for now, we can implement logic to mark in_use and conflict based on actual usage in the system
            })

            # Option 4: extended rule
            first_part = token_lower[:4]
            rest_part = re.sub(r'[aeiou]', '', token_lower[4:]) if len(token_lower) > 4 else ''
            abbr3 = (first_part + rest_part)[:8].capitalize()
            conflict3 = abbr3 in new_abbreviations.values() or abbr3 in abbreviations.values()
            options.append({
                "value": abbr3,
                "in_use": False,
                "conflict": False #All False for now, we can implement logic to mark in_use and conflict based on actual usage in the system
            })

            words_options[token] = options
            new_abbreviations[token_lower] = abbr2

        return {"words_options": words_options}


    def gen_var_name(self, **kwargs):
        values = {}
        warnings_list = []

        for field in self.fields:

            if field == "description":
                description_tokens = kwargs.get("description", {})

                # Keep order as received
                final_tokens = list(description_tokens.values())
                if final_tokens:
                    final_tokens[0] = final_tokens[0].lower()

                stitched_description = "".join(final_tokens)
                values["description"] = stitched_description

            else:
                user_input = kwargs.get(field, "")
                mapping_file = os.path.join(self.base_path, f"{field}s.json")
                mapping = self._safe_load(mapping_file)
                values[field] = mapping.get(user_input, user_input)

        # Build final variable name
        variable_name = self.template.format(**values)

        # Always check length
        if len(variable_name) > 31:
            warnings_list.append(
                f"Final variable name must be less than 31 characters. Current length: {len(variable_name)}"
            )

        # ---------------------------
        # Insert into Database
        # ---------------------------
        variable_id = None
        try:
            variable_id = DatabaseService.insert_variable_name(
                variable_name=variable_name,
                module=values.get("module"),
                data_type=values.get("data_type"),
                data_size=values.get("data_size"),
                unit=values.get("unit"),
                description_user=kwargs.get("description_user"),
                description_json=None
            )
        except sqlite3.IntegrityError as e:
            # Duplicate variable name
            if "UNIQUE constraint failed" in str(e):
                warnings_list.append(f'"{variable_name}" already exists')
                variable_id = None
            else:
                raise  # re-raise any other DB integrity errors

        # Insert abbreviations snapshot only if variable_id is valid
        if variable_id:
            description_tokens = kwargs.get("description", {})
            for word, abbr in description_tokens.items():
                DatabaseService.insert_abbreviation(word, abbr, variable_id)

        return {
            "variable_name": variable_name,
            "warnings": warnings_list,
            "variable_id": variable_id
        }



#end of NamingService class