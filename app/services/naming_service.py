# app/services/naming_service.py
import json
import re
import os


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



    # ---------------------------
    # Public API Methods
    # ---------------------------

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

    def get_pending(self):
        return self._safe_load(os.path.join(self.standard_path, "pending.json"))

    def admin_action(self, body: dict):
        variables = body.get("variables", [])
        action = body.get("action", "")

        if action == "approve":
            approved = self._approve_pending_abbreviations(variables)
            return {"status": "approved", "approved": approved}

        if action == "delete":
            self._delete_pending_abbreviations(variables)
            return {"status": "deleted", "deleted": variables}

        return {"status": "error", "message": "Invalid action"}

    def get_stats(self):
        return self._safe_load(self.endpoint_counts_path)

    # ---------------------------
    # Core Naming Logic
    # ---------------------------

    def _load_abbreviation(self):
        path = os.path.join(self.standard_path, "abbreviation.json")
        data = self._safe_load(path)
        return {k.lower(): v for k, v in data.items()}

    def _add_new_abbreviations(self, new_abbrs: dict):
        pending_path = os.path.join(self.standard_path, "pending.json")
        pending = self._safe_load(pending_path)

        for word, abbr in new_abbrs.items():
            if word not in pending:
                pending[word] = abbr

        self._safe_save(pending_path, pending)


    # ---------------------------
    # Admin Internal
    # ---------------------------

    def _approve_pending_abbreviations(self, to_approve: list):
        pending_path = os.path.join(self.standard_path, "pending.json")
        approved_path = os.path.join(self.standard_path, "abbreviation.json")

        pending = self._safe_load(pending_path)
        approved = self._safe_load(approved_path)

        approved_items = {}

        for word in to_approve:
            if word in pending:
                approved[word] = pending[word]
                approved_items[word] = pending[word]
                del pending[word]

        self._safe_save(approved_path, approved)
        self._safe_save(pending_path, pending)

        return approved_items

    def _delete_pending_abbreviations(self, to_delete: list):
        pending_path = os.path.join(self.standard_path, "pending.json")
        pending = self._safe_load(pending_path)

        for word in to_delete:
            pending.pop(word, None)

        self._safe_save(pending_path, pending)

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
                "in_use": True,               # can mark as in use
                "conflict": False
            })

            # Option 2: JSON dictionary abbreviation (existing)
            if token_lower in abbreviations:
                options.append({
                    "value": abbreviations[token_lower],
                    "in_use": True,
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
                "conflict": conflict2
            })

            # Option 4: extended rule
            first_part = token_lower[:4]
            rest_part = re.sub(r'[aeiou]', '', token_lower[4:]) if len(token_lower) > 4 else ''
            abbr3 = (first_part + rest_part)[:8].capitalize()
            conflict3 = abbr3 in new_abbreviations.values() or abbr3 in abbreviations.values()
            options.append({
                "value": abbr3,
                "in_use": False,
                "conflict": conflict3
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

                # 🔴 Description length validation (14–22)
                desc_length = len(stitched_description)
                if not (14 <= desc_length <= 22):
                    warnings_list.append(
                        f"Description length should be between 14 and 22 characters. "
                        f"Current length: {desc_length}"
                    )

            else:
                user_input = kwargs.get(field, "")

                mapping_file = os.path.join(self.base_path, f"{field}s.json")
                mapping = self._safe_load(mapping_file)

                values[field] = mapping.get(user_input, user_input)

        # Build final variable name
        variable_name = self.template.format(**values)

        # 🔴 Final variable name must be 31 characters
        var_length = len(variable_name)
        if var_length > 31:
            warnings_list.append(
                f"Final variable name must be less than 31 characters. "
                f"Current length: {var_length}"
            )

        return {
            "variable_name": variable_name,
            "warnings": warnings_list
        }