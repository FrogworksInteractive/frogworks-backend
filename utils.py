import uuid
import random
import bcrypt

from datetime import date

from structures.application_key import ApplicationKey
from structures.application_session import ApplicationSession
from structures.application_version import ApplicationVersion
from structures.cloud_data import CloudData
from structures.deposit import Deposit
from structures.friend import Friend
from structures.friend_request import FriendRequest
from structures.iap import IAP
from structures.invite import Invite
from structures.photo import Photo
from structures.purchase import Purchase
from structures.sale import Sale
from structures.session import Session
from structures.structure import Structure
from structures.transaction import Transaction
from structures.user import User


class Utils:
    @staticmethod
    def generate_product_key() -> str:
        # Return a product key (UUID) with the format:
        # XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
        return str(uuid.uuid4()).upper()

    @staticmethod
    def generate_uuid4() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def generate_session_identifier() -> str:
        return uuid.uuid4().hex

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

    @staticmethod
    def date_between(date_: date, start_date: date, end_date: date) -> bool:
        return start_date <= date_ <= end_date

    @staticmethod
    def safe_int_cast(value, default: int = 0) -> int:
        try:
            return int(value)
        except ValueError:
            return default

    @staticmethod
    def safe_float_cast(value, default: float = 0) -> float:
        try:
            return float(value)
        except ValueError:
            return default

    @staticmethod
    def safe_bool_cast(value, default: bool = False) -> bool:
        if str(value).lower() in ['true', 'false']:
            return str(value).lower() == 'true'

        try:
            return bool(value)
        except ValueError:
            return default

    @staticmethod
    def serialize(item, private: bool):
        if isinstance(item, Structure):
            return item.into_dict(private)
        elif isinstance(item, bool):
            return 'true' if item else 'false'
        elif isinstance(item, dict):
            # Copy the dictionary to avoid issues because Python is special.
            item_copy = item.copy()

            # Loop through the dictionary contents, serializing them along the way.
            for key, value in item_copy.items():
                item_copy[key] = Utils.serialize(value, private)

            return item_copy
        elif isinstance(item, list):
            serialized_item = []

            # Loop through and serialize every item in the array.
            for i in item:
                serialized_item.append(Utils.serialize(i, private))

            return serialized_item
        elif type(item) in [int, float]:
            return item

        # As a catch-all, turn the item into a string.
        # This will work for dates and whatever else gets to this point.
        # Custom logic can be implemented for anything that should not get to this point, in the above if-elseif chain.
        return str(item)

    @staticmethod
    def row_to_user(row: dict) -> User:
        return User(
            row['id'],
            row['identifier'],
            row['username'],
            row['name'],
            row['email_address'],
            row['password'],
            row['joined'],
            row['balance'],
            row['profile_photo_id'],
            row['activity'],
            row['developer'],
            row['administrator'],
            row['verified']
        )

    @staticmethod
    def row_to_application_version(row: dict) -> ApplicationVersion:
        return ApplicationVersion(
            row['id'],
            row['application_id'],
            row['name'],
            row['platform'],
            row['release_date'],
            row['filename'],
            row['executable']
        )

    @staticmethod
    def row_to_sale(row: dict) -> Sale:
        return Sale(
            row['id'],
            row['application_id'],
            row['title'],
            row['description'],
            row['price'],
            row['start_date'],
            row['end_date']
        )

    @staticmethod
    def row_to_purchase(row: dict) -> Purchase:
        return Purchase(
            row['id'],
            row['application_id'],
            row['iap_id'],
            row['user_id'],
            row['type'],
            row['source'],
            row['price'],
            row['key'],
            row['date']
        )

    @staticmethod
    def row_to_deposit(row: dict) -> Deposit:
        return Deposit(
            row['id'],
            row['user_id'],
            row['amount'],
            row['source'],
            row['date']
        )

    @staticmethod
    def row_to_transaction(row: dict) -> Transaction:
        return Transaction(
            row['id'],
            row['user_id'],
            row['transaction_id'],
            row['type'],
            row['date']
        )

    @staticmethod
    def row_to_application_key(row: dict) -> ApplicationKey:
        return ApplicationKey(
            row['id'],
            row['application_id'],
            row['key'],
            row['type'],
            row['redeemed'],
            row['user_id']
        )

    @staticmethod
    def row_to_friend_request(row: dict) -> FriendRequest:
        return FriendRequest(
            row['id'],
            row['user_id'],
            row['from_user_id'],
            row['date']
        )

    @staticmethod
    def row_to_friend(row: dict) -> Friend:
        return Friend(
            row['id'],
            row['user_id'],
            row['other_user_id'],
            row['date']
        )

    @staticmethod
    def row_to_session(row: dict) -> Session:
        return Session(
            row['id'],
            row['identifier'],
            row['user_id'],
            row['hostname'],
            row['mac_address'],
            row['platform'],
            row['start_date'],
            row['last_activity'],
        )

    @staticmethod
    def row_to_invite(row: dict) -> Invite:
        return Invite(
            row['id'],
            row['user_id'],
            row['from_user_id'],
            row['application_id'],
            row['details'],
            row['date']
        )

    @staticmethod
    def row_to_application_session(row: dict) -> ApplicationSession:
        return ApplicationSession(
            row['id'],
            row['user_id'],
            row['application_id'],
            row['date'],
            row['length']
        )

    @staticmethod
    def row_to_photo(row: dict) -> Photo:
        return Photo(
            row['id'],
            row['filename'],
            row['subfolder'],
            row['created_at']
        )

    @staticmethod
    def row_to_iap(row: dict) -> IAP:
        return IAP(
            row['id'],
            row['application_id'],
            row['title'],
            row['description'],
            row['price'],
            row['data']
        )

    @staticmethod
    def row_to_cloud_data(row: dict) -> CloudData:
        return CloudData(
            row['id'],
            row['user_id'],
            row['application_id'],
            row['data'],
            row['date']
        )
