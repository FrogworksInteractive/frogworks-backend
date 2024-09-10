import json
import sqlite3
from datetime import date

from email_manager import EmailManager
from utils import Utils


class Database:
    def __init__(self, email_manager: EmailManager):
        self.path: str = 'frogworks.db'
        self.initialized: bool = False
        self.connection = None
        self.cursor = None
        self.email_manager: EmailManager = email_manager

    def initialize(self):
        if not self.initialized:
            # Connect to the SQLite database.
            self.connection = sqlite3.connect(self.path)
            self.cursor = self.connection.cursor()

            # Set the cursor's row factory so queries return dicts instead of arrays.
            self.cursor.row_factory = Utils.dict_factory

            # Ensure that the necessary tables have been created.
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `users` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `identifier` TEXT NOT NULL,
                `username` TEXT NOT NULL,
                `name` TEXT NOT NULL,
                `email_address` TEXT NOT NULL,
                `password` TEXT NOT NULL,
                `joined` DATE NOT NULL,
                `balance` TEXT NOT NULL,
                `profile_photo_id` INTEGER NOT NULL,
                `activity` TEXT NOT NULL -- JSON information.
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `applications` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `name` TEXT NOT NULL,
                `type` TEXT NOT NULL,
                `description` TEXT NOT NULL,
                `release_date` DATE NOT NULL,
                `early_access` BOOLEAN NOT NULL,
                `latest_version` TEXT NOT NULL,
                `supported_platforms` TEXT NOT NULL,
                `genres` TEXT NOT NULL,
                `tags` TEXT NOT NULL,
                `base_price` TEXT NOT NULL,
                `owners` TEXT NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `sales` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `application_id` INTEGER NOT NULL,
                `title` TEXT NOT NULL,
                `description` TEXT NOT NULL,
                `price` TEXT NOT NULL,
                `start_date` DATE NOT NULL,
                `end_date` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `purchases` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `application_id` INTEGER NOT NULL,
                `user_id` INTEGER NOT NULL,
                `type` TEXT NOT NULL, -- game, iap
                `source` TEXT NOT NULL, -- local, gift
                `price` TEXT NOT NULL,
                `key` TEXT NOT NULL,
                `date` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `deposits` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `user_id` INTEGER NOT NULL,
                `amount` TEXT NOT NULL,
                `source` TEXT NOT NULL, -- purchase, gift
                `date` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `transactions` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `user_id` INTEGER NOT NULL,
                `transaction_id` INTEGER NOT NULL,
                `type` TEXT NOT NULL, -- purchase, deposit
                `date` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `application_keys` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `application_id` INTEGER NOT NULL,
                `key` TEXT NOT NULL,
                `type` TEXT NOT NULL, -- purchase, creator
                `redeemed` BOOLEAN NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `friend_requests` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `user_id` INTEGER NOT NULL,
                `from_user_id` INTEGER NOT NULL,
                `date` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `friends` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `user_id` INTEGER NOT NULL,
                `other_user_id` INTEGER NOT NULL,
                `date` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `sessions` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `user_id` INTEGER NOT NULL,
                `hostname` TEXT NOT NULL,
                `mac_address` TEXT NOT NULL,
                `platform` TEXT NOT NULL,
                `start_date` DATE NOT NULL,
                `last_activity` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `invites` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `user_id` INTEGER NOT NULL,
                `from_user_id` INTEGER NOT NULL,
                `application_id` INTEGER NOT NULL,
                `details` TEXT NOT NULL,
                `date` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `application_sessions` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `user_id` INTEGER NOT NULL,
                `application_id` INTEGER NOT NULL,
                `date` DATE NOT NULL,
                `length` INTEGER NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `photos` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `filename` TEXT NOT NULL,
                `subfolder` TEXT NOT NULL,
                `created_at` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `iaps` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `application_id` INTEGER NOT NULL,
                `title` TEXT NOT NULL,
                `description` TEXT NOT NULL,
                `price` TEXT NOT NULL,
                `data` TEXT NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `email_codes` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `email_address` TEXT NOT NULL,
                `code` INTEGER NOT NULL
            )
            ''')

        self.initialized = True

    def username_taken(self, username: str) -> bool:
        # Check if a user exists with that username.
        self.cursor.execute('SELECT FROM `users` WHERE `username` = ? COLLATE NOCASE', (username,))
        row = self.cursor.fetchone()

        return not row is None

    def email_taken(self, email: str) -> bool:
        # Check if a user exists with that email address.
        self.cursor.execute('SELECT FROM `users` WHERE `email_address` = ? COLLATE NOCASE', (email,))
        row = self.cursor.fetchone()

        return not row is None

    def check_email_verification(self, email_address: str, provided_code: int) -> bool:
        # Get the email's verification code.
        self.cursor.execute('SELECT * FROM `email_codes` WHERE `email_address` = ? COLLATE NOCASE', (email_address,))
        row = self.cursor.fetchone()

        if row is None:
            # A code has not even been requested for the specified email address.
            return False


    def request_email_verification_code(self, email_address: str):
        # Delete all previous verification codes for the specified email.
        pass

    def create_user(self, username: str, name: str, email_address: str, password: str,
                    email_verification_code: int) -> tuple[bool, dict]:
        # Perform the pre-registration checks.
        if self.username_taken(username):
            return False, {'details': 'This username is already taken.'}
        elif self.email_taken(email_address):
            return False, {'details': 'This email address is already taken.'}
        elif not self.check_email_verification(email_address, email_verification_code):
            return False, {'details': 'Invalid verification code.'}

        # Everything is okay, continue with the registration.

        # Generate the user's identifier.
        identifier: str = Utils.generate_user_identifier()

        # Hash the user's password.
        hashed_password: str = Utils.hash_password(password)

        # Get the current date.
        current_date: date = date.today()

        # Initialize the other properties with default values.
        balance: str = '0'
        profile_photo_id: int = 1
        activity: dict = Utils.generate_activity_dict(-1, '', {})

        # Create the user's account.
        self.cursor.execute('''
        INSERT INTO `users` (`identifier`, `username`, `name`, `email_address`, `password`, `joined`, `balance`, `profile_photo_id`, `activity`)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (identifier, username, name, email_address, hashed_password, current_date, balance, profile_photo_id, json.dumps(activity)))

        return True, {'details': 'User created successfully.'}
