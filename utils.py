import uuid
import random

import bcrypt


class Utils:
    @staticmethod
    def generate_product_key() -> str:
        # Return a product key (UUID) with the format:
        # XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
        return str(uuid.uuid4()).upper()

    @staticmethod
    def hash_password(password: str) -> str:
        # Generate a salt for the hash so that no one can tell if two passwords are the same.
        salt = bcrypt.gensalt()

        # Hash and return the password.
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def password_matches(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def generate_user_identifier() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def generate_activity_dict(application_id: int, description: str, details: dict) -> dict:
        return {
            'application_id': application_id,
            'description': description,
            'details': details
        }

    @staticmethod
    def generate_verification_code() -> int:
        return random.randint(100000, 999999)

    # Source: https://stackoverflow.com/a/3300514
    # Reason: So I can get a dictionary from an SQLite query instead of a non-associative array.
    @staticmethod
    def dict_factory(cursor, row):
        d = {}

        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]

        return d
