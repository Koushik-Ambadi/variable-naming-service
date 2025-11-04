# app/services/naming_service.py
import json
import re
import os

class NamingService:

# Variable Naming Logic:

    STOPWORDS = [
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "do", "does", "doing", "down", "during",
        "each", "few", "for", "from", "further", "had", "has", "have", "he", "her", "here",
        "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
        "it", "its", "itself", "let's", "me", "more", "most", "my", "myself",
        "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
        "our", "ours", "ourselves", "out", "over", "own", "same", "she",
        "should", "so", "some", "such", "than", "that", "the", "their", "theirs",
        "them", "themselves", "then", "there", "these", "they", "this", "those",
        "through", "to", "too", "under", "until", "up", "very", "was", "we",
        "were", "what", "when", "where", "which", "while", "who", "whom", "why",
        "with", "would", "you", "your", "yours", "yourself", "yourselves",
        "used", "in", "of", "for", "with", "from", "to", "by", "on", "at", "as",
        "into", "over", "under", "between", "through", "via", "about", "per",
        "within", "without", "along", "across", "among", "behind", "against",
        "toward", "up", "down", "around", "near", "inside", "outside"
    ]

    def __init__(self, format: str = "abs", standard: str = "autosar"):
        self.format = format
        self.standard = standard
        self.base_path = os.path.join(os.getcwd(), f"data/naming_conventions/{self.format}")
        self.config = self._load_json("format.json")

        self.fields = self.config["fields"]
        self.template = self.config["template"]
        self.mappings = self._load_all_mappings()

        # Define data path for storing the endpoint counts
        self.data_path = os.path.join(os.getcwd(), "data")  # This is where 'endpoint_counts.json' will be stored
        self.endpoint_counts_path = os.path.join(self.data_path, "endpoint_counts.json")

    def _load_json(self, relative_path: str):
        full_path = os.path.join(self.base_path, relative_path)
        with open(full_path, "r") as f:
            return json.load(f)

    def _load_all_mappings(self):
        mappings = {}
        for field in self.fields:
            file_path = os.path.join(self.base_path, f"{field}s.json")
            if os.path.exists(file_path):
                mappings[field] = self._load_json(f"{field}s.json")
        return mappings

    def _load_abbreviation(self, standard: str):
        abbr_path = os.path.join(os.getcwd(), f"data/standards/{standard}/abbreviation.json")
        if os.path.exists(abbr_path):
            with open(abbr_path, "r") as f:
                return {k.lower(): v for k, v in json.load(f).items()}
        return {}

    def _add_new_abbreviations(self, standard: str, new_abbrs: dict):
        pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")

        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                try:
                    pending = json.load(f)
                except json.JSONDecodeError:
                    pending = {}
        else:
            pending = {}

        updated = False
        for word, abbr in new_abbrs.items():
            if word not in pending:
                pending[word] = abbr
                updated = True

        if updated:
            with open(pending_path, "w") as f:
                json.dump(pending, f, indent=4)

    def gen_var_name(self, standard: str = None, **kwargs):
        standard = standard or self.standard
        abbreviations = self._load_abbreviation(standard)

        values = {}
        autosar_matches = []
        new_abbreviations = {}

        for field in self.fields:
            user_input = kwargs.get(field, "")

            if field == "description":
                tokens = user_input.split()
                final_tokens = []

                for token in tokens:
                    token_lower = token.lower()
                    if token_lower in abbreviations:
                        abbr = abbreviations[token_lower]
                        autosar_matches.append({
                            "word": token,
                            "replacement": abbr,
                        })
                    elif token_lower in self.STOPWORDS:
                        abbr = ""
                    else:
                        first = token_lower[0]
                        rest = re.sub(r'[aeiou]', '', token_lower[1:])
                        rest = re.sub(r'(.)\1+', r'\1', rest)
                        abbr = (first + rest)[:4].capitalize()
                        new_abbreviations[token_lower] = abbr

                    final_tokens.append(abbr)

                final_variable = "".join([t for t in final_tokens if t])
                if new_abbreviations:
                    self._add_new_abbreviations(standard, new_abbreviations)
                values[field] = final_variable
            else:
                mapping = self.mappings.get(field, {})
                values[field] = mapping.get(user_input, user_input)

        variable_name = self.template.format(**values)
        return {
            "variable_name": variable_name,
            "autosar_matches": autosar_matches
        }

# Admin Logic:

    def _approve_pending_abbreviations(self, standard: str, to_approve: list):
        """
        Move entries from pending.json to abbreviation.json (approved),
        then delete those entries from pending.json
        """
        pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
        approved_path = os.path.join(os.getcwd(), f"data/standards/{standard}/abbreviation.json")

        # Load pending
        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                try:
                    pending = json.load(f)
                except json.JSONDecodeError:
                    pending = {}
        else:
            pending = {}

        # Load approved
        if os.path.exists(approved_path):
            with open(approved_path, "r") as f:
                try:
                    approved = json.load(f)
                except json.JSONDecodeError:
                    approved = {}
        else:
            approved = {}

        approved_items = {}
        updated = False

        for word in to_approve:
            if word in pending:
                approved[word] = pending[word]
                approved_items[word] = pending[word]
                del pending[word]
                updated = True

        if updated:
            # Save updated approved
            with open(approved_path, "w") as f:
                json.dump(approved, f, indent=4)

            # Save updated pending
            with open(pending_path, "w") as f:
                json.dump(pending, f, indent=4)

        return approved_items


    def _delete_pending_abbreviations(self, standard: str, to_delete: list):
        """Delete multiple entries from pending.json"""
        pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")

        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                try:
                    pending = json.load(f)
                except json.JSONDecodeError:
                    pending = {}
        else:
            pending = {}

        updated = False
        for word in to_delete:
            if word in pending:
                del pending[word]
                updated = True

        if updated:
            with open(pending_path, "w") as f:
                json.dump(pending, f, indent=4)



# EndpointUsageTracker:
    def update_endpoint_count(self, endpoint: str):
        """This function updates the count of hits for a given endpoint."""
        
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        
        # Load the existing endpoint counts
        if os.path.exists(self.endpoint_counts_path):
            try:
                with open(self.endpoint_counts_path, "r", encoding="utf-8") as f:
                    endpoint_counts = json.load(f)
            except json.JSONDecodeError:
                endpoint_counts = {}
        else:
            endpoint_counts = {}

        # Increment the count for the given endpoint
        if endpoint in endpoint_counts:
            endpoint_counts[endpoint] += 1
        else:
            endpoint_counts[endpoint] = 1

        # Save the updated counts back to the file
        try:
            with open(self.endpoint_counts_path, "w", encoding="utf-8") as f:
                json.dump(endpoint_counts, f, indent=4)
        except Exception as e:
            print(f"Error saving endpoint counts: {e}")