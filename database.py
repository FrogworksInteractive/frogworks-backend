import json
import sqlite3

from datetime import date, datetime
from loguru import logger

from email_manager import EmailManager
from email_utils import EmailUtils
from structures.iap_record import IAPRecord
from structures.application import Application
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
from structures.transaction import Transaction
from structures.user import User
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
            logger.info('Connecting to the SQLite database.')
            self.connection = sqlite3.connect(self.path, check_same_thread=False)
            self.cursor = self.connection.cursor()

            # Set the cursor's row factory so queries return dicts instead of arrays.
            self.cursor.row_factory = Utils.dict_factory

            logger.info('Creating nonexistent database tables.')

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
                `activity` TEXT NOT NULL, -- JSON information.
                `developer` BOOLEAN NOT NULL,
                `administrator` BOOLEAN NOT NULL,
                `verified` BOOLEAN NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `applications` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `name` TEXT NOT NULL,
                `package_name` TEXT NOT NULL,
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
            CREATE TABLE IF NOT EXISTS `application_versions` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `application_id` INTEGER NOT NULL,
                `name` TEXT NOT NULL,
                `platform` TEXT NOT NULL,
                `release_date` DATE NOT NULL,
                `filename` TEXT NOT NULL,
                `executable` TEXT NOT NULL
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
                `iap_id` INTEGER NOT NULL, -- If N/A: -1
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
                `redeemed` BOOLEAN NOT NULL,
                `user_id` INTEGER NOT NULL
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
                `identifier` TEXT NOT NULL,
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

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `cloud_data` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `user_id` INTEGER NOT NULL,
                `application_id` INTEGER NOT NULL,
                `data` TEXT NOT NULL,
                `date` DATE NOT NULL
            )
            ''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS `iap_records` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `iap_id` INTEGER NOT NULL,
                `user_id` INTEGER NOT NULL,
                `application_id` INTEGER NOT NULL,
                `date` DATE NOT NULL,
                `acknowledged` BOOLEAN NOT NULL
            )
            ''')

        self.initialized = True

    def username_taken(self, username: str) -> bool:
        # Check if a user exists with that username.
        self.cursor.execute('SELECT * FROM `users` WHERE `username` = ? COLLATE NOCASE', (username,))
        row = self.cursor.fetchone()

        return not row is None

    def email_taken(self, email: str) -> bool:
        # Check if a user exists with that email address.
        self.cursor.execute('SELECT * FROM `users` WHERE `email_address` = ? COLLATE NOCASE', (email,))
        row = self.cursor.fetchone()

        return not row is None

    def check_email_verification(self, email_address: str, provided_code: int) -> bool:
        # Get the email's verification code.
        self.cursor.execute('SELECT * FROM `email_codes` WHERE `email_address` = ? COLLATE NOCASE', (email_address,))
        row = self.cursor.fetchone()

        if row is None:
            # A code has not even been requested for the specified email address.
            return False

        return row['code'] == provided_code

    def request_email_verification_code(self, email_address: str):
        # Delete all previous verification codes for the specified email.
        self.delete_email_verification_codes_for(email_address)

        # Generate a new verification code.
        verification_code: int = Utils.generate_verification_code()
        logger.info(f'Generated verification code for {email_address}: {verification_code}')

        # Insert the new verification code into the database.
        self.cursor.execute('INSERT INTO `email_codes` (`email_address`, `code`) VALUES (?, ?)', (email_address, verification_code))

        # Commit the changes.
        self.connection.commit()

        # Generate the verification email.
        subject, text, html = EmailUtils.generate_email(
            'Frogworks Email Verification',
            'Email Verification',
            f'Your email verification code is: <b>{verification_code}</b>',
            'Do not give this code to anyone.'
        )

        # Send the verification email.
        self.email_manager.send_email(
            subject,
            text,
            html,
            [email_address]
        )

    def delete_email_verification_codes_for(self, email_address: str):
        # Delete all verification codes for the specified email address.
        self.cursor.execute('DELETE FROM `email_codes` WHERE `email_address` = ? COLLATE NOCASE', (email_address,))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Deleting email verification code for {email_address}')


    def package_name_taken(self, package_name: str) -> bool:
        # Check if an application exists with that package name.
        self.cursor.execute('SELECT * FROM `applications` WHERE `package_name` = ? COLLATE NOCASE', (package_name,))
        row = self.cursor.fetchone()

        return not row is None

    def create_user(self, username: str, name: str, email_address: str, password: str,
                    email_verification_code: int, **kwargs) -> tuple[bool, dict]:
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
        profile_photo_id: int = 0
        activity: dict = Utils.generate_activity_dict(-1, '', {})

        # Handle the kwargs.
        developer: bool = kwargs.get('developer', False)
        administrator: bool = kwargs.get('administrator', False)
        verified: bool = kwargs.get('verified', False)

        # Create the user's account.
        self.cursor.execute('''
        INSERT INTO `users` (`identifier`, `username`, `name`, `email_address`, `password`, `joined`, `balance`, `profile_photo_id`, `activity`, `developer`, `administrator`, `verified`)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (identifier, username, name, email_address, hashed_password, current_date, balance, profile_photo_id, json.dumps(activity), developer, administrator, verified))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Created user: {username} - name: {name}, email address: {email_address}, '
                    f'identifier: {identifier}')

        # Delete the user's email verification code so that it cannot be used again.
        self.delete_email_verification_codes_for(email_address)

        # Generate the registration email.
        subject, text, html = EmailUtils.generate_email(
            'Welcome to Frogworks!',
            'Account Created',
            f'Thank you for joining Frogworks! We are glad to have you!<br><br>Let\'s go over your account '
            f'details just so you\'re aware!<br>Frogworks ID: {identifier}<br>Username: {username}',
            'You can modify most parts of your account at any time.'
        )

        # Send the registration email.
        self.email_manager.send_email(
            subject,
            text,
            html,
            [email_address]
        )

        return True, {'details': 'User created successfully.'}

    def get_user(self, identifier, identifier_type: str = 'id') -> User | None:
        # Ensure that the identifier type is valid.
        if not identifier_type in ['id', 'identifier', 'username', 'email_address']:
            return None

        # Attempt to fetch the user from the provided identifier.
        self.cursor.execute(f'SELECT * FROM `users` WHERE `{identifier_type}` = ? COLLATE NOCASE', (identifier,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_user(row)

    def update_user_property(self, user_id: int, property_: str, value):
        # Attempt to update the user.
        self.cursor.execute(f'UPDATE `users` SET `{property_}` = ? WHERE `id` = ?', (value, user_id))

        # Commit the changes.
        self.connection.commit()

    def create_application(self, name: str, package_name: str, type_: str, description: str, release_date: date,
                           early_access: bool, latest_version: str, supported_platforms: list, genres: list, tags: list,
                           base_price: float, owners: list) -> tuple[bool, dict]:
        # Make sure the package name is not taken.
        if self.package_name_taken(package_name):
            return False, {'details': 'This package name is already taken.'}

        # Combine the lists into strings separated by commas.
        supported_platforms_string: str = ','.join(supported_platforms)
        genres_string: str = ','.join(genres)
        tags_string: str = ','.join(tags)
        owners_string: str = ','.join(owners)

        # Convert the base price to a string.
        base_price_string = str(base_price)

        # Create the application.
        self.cursor.execute('''
        INSERT INTO `applications` (`name`, `package_name`, `type`, `description`, `release_date`, `early_access`, `latest_version`, `supported_platforms`, `genres`, `tags`, `base_price`, `owners`)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, package_name, type_, description, release_date, early_access, latest_version, supported_platforms_string, genres_string, tags_string, base_price_string, owners_string))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Created application: {name} - type: {type_}, description: {description}, '
                    f'early access: {early_access}, supported platforms: {supported_platforms_string}, '
                    f'genres: {genres_string}, tags: {tags_string}, owners: {owners_string}')

        return True, {'details': 'Application created successfully.', 'application_id': self.cursor.lastrowid}

    def get_application(self, identifier, identifier_type: str = 'id') -> Application | None:
        # Ensure that the identifier type is valid.
        if not identifier_type in ['id', 'package_name']:
            return None

        self.cursor.execute(f'SELECT * FROM `applications` WHERE `{identifier_type}` = ? COLLATE NOCASE', (identifier,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_application(row)

    def get_all_applications(self) -> list[Application]:
        # Fetch all applications.
        applications: list[Application] = []

        self.cursor.execute('SELECT * FROM `applications`')

        for row in self.cursor.fetchall():
            applications.append(Utils.row_to_application(row))

        return applications

    def update_application_property(self, application_id: int, property_: str, value):
        # Attempt to update the specified application.
        self.cursor.execute(f'UPDATE `applications` SET `{property_}` = ? WHERE `id` = ?', (value, application_id))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Updated application ({application_id}) property: {property_} - value: {value}')

    def create_application_version(self, application_id: int, name: str, platform: str, release_date: date,
                                   filename: str, executable: str) -> tuple[bool, dict]:
        # Make sure the version does not already exist.
        fetched_version = self.get_application_version(application_id, name, platform)

        if fetched_version:
            return False, {'details': 'Application version already exists.'}

        # The version does not exist; proceed with the creation.
        self.cursor.execute('''
        INSERT INTO `application_versions` (`application_id`, `name`, `platform`, `release_date`, `filename`, `executable`)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (application_id, name, platform, release_date, filename, executable))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Creating application version. Application id: {application_id}, version name: {name}, '
                    f'platform: {platform}, release_date: {release_date}, filename: {filename}, '
                    f'executable: {executable}')

        return True, {'details': 'Application version created successfully.'}

    def get_application_version(self, application_id: int, version_name: str,
                                platform: str) -> ApplicationVersion | None:
        # Attempt to get an application version that matches the provided application, version name, and platform.
        self.cursor.execute('''SELECT * FROM `application_versions` WHERE `application_id` = ? AND `name` = ? AND `platform` = ? COLLATE NOCASE''', (application_id, version_name, platform))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_application_version(row)

    def get_application_versions(self, application_id: int) -> list[ApplicationVersion]:
        versions: list[ApplicationVersion] = []

        # Fetch all versions for a specified application.
        self.cursor.execute('SELECT * FROM `application_versions` WHERE `application_id` = ?', (application_id,))

        for row in self.cursor.fetchall():
            versions.append(Utils.row_to_application_version(row))

        return versions

    def get_application_versions_for_platform(self, application_id: int, platform: str) -> list[ApplicationVersion]:
        versions: list[ApplicationVersion] = []

        # Fetch all versions for a specified application.
        self.cursor.execute('SELECT * FROM `application_versions` WHERE `application_id` = ? AND `platform` = ?', (application_id, platform))

        for row in self.cursor.fetchall():
            versions.append(Utils.row_to_application_version(row))

        return versions

    def get_application_version_by_id(self, version_id: int) -> ApplicationVersion | None:
        # Attempt to get an application version from the provided id.
        self.cursor.execute('SELECT * FROM `application_versions` WHERE `id` = ?', (version_id,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_application_version(row)

    def create_sale(self, application_id: int, title: str, description: str, price: float, start_date: date,
                    end_date: date) -> tuple[bool, dict]:
        # Ensure that a sale will not be active between the specified dates.
        start_date_sale = self.get_active_sale(application_id, start_date)

        if start_date_sale:
            return False, {'details': 'A sale will already be active during the specified dates.'}

        end_date_sale = self.get_active_sale(application_id, end_date)

        if end_date_sale:
            return False, {'details': 'A sale will already be active during the specified dates.'}

        # A sale will not be active during the specified dates; continue with the creation.
        # Convert the price to a string for storage in the database.
        price_string: str = str(price)

        # Create the sale.
        self.cursor.execute('''
        INSERT INTO `sales` (`application_id`, `title`, `description`, `price`, `start_date`, `end_date`)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (application_id, title, description, price_string, start_date, end_date))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Created sale for application: {application_id} - title: {title}, description: {description}, '
                    f'price: {price_string}, start date: {start_date}, end date: {end_date}')

        return True, {'details': 'Sale created successfully.'}

    def delete_sale(self, id_: int) -> tuple[bool, dict]:
        # Ensure that the sale exists.
        if self.get_sale(id_) is None:
            return False, {'details': 'Sale does not exist.'}

        # Delete the sale.
        self.cursor.execute('DELETE FROM `sales` WHERE `id` = ?', (id_,))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Deleted sale: {id_}')

        return True, {'details': 'Sale deleted successfully.'}

    def get_active_sale(self, application_id: int, active_date: date) -> Sale | None:
        # Get all sales for the specified application.
        self.cursor.execute('SELECT * FROM `sales` WHERE `application_id` = ?', (application_id,))

        # Loop through all the sales, looking for one that is active during the specified date.
        for row in self.cursor.fetchall():
            # Check if the sale is active during the specified date.
            start_date = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(row['end_date'], '%Y-%m-%d').date()

            if Utils.date_between(active_date, start_date, end_date):
                return Utils.row_to_sale(row)

        return None

    def get_sale(self, id_: int) -> Sale | None:
        # Attempt to get the sale from the provided id.
        self.cursor.execute('SELECT * FROM `sales` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_sale(row)

    def get_sales_for(self, application_id: int) -> list[Sale]:
        sales: list[Sale] = []

        # Fetch all sales for the specified application.
        self.cursor.execute('SELECT * FROM `sales` WHERE `application_id` = ?', (application_id,))

        # Loops through all the results, convert them to a sale, and add them to the list.
        for row in self.cursor.fetchall():
            sales.append(Utils.row_to_sale(row))

        return sales

    def create_purchase(self, application_id: int, iap_id: int, user_id: int, type_: str, source: str, price: str,
                        key: str, date_: date) -> int:
        # Create the purchase record.
        self.cursor.execute('''
        INSERT INTO `purchases` (`application_id`, `iap_id`, `user_id`, `type`, `source`, `price`, `key`, `date`)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (application_id, iap_id, user_id, type_, source, price, key, date_))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'User: {user_id} purchased {application_id} ({iap_id}) - type: {type_}, source: {source}, '
                    f'price: {price}, key: {key}, date: {date_}')

        return self.cursor.lastrowid

    def get_purchase(self, id_: int) -> Purchase | None:
        # Attempt to get the requested purchase.
        self.cursor.execute('SELECT * FROM `purchases` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_purchase(row)

    def create_deposit(self, user_id: int, amount: float, source: str, date_: date) -> int:
        # Create the deposit record.
        self.cursor.execute('''
        INSERT INTO `deposits` (`user_id`, `amount`, `source`, `date`)
        VALUES (?, ?, ?, ?)
        ''', (user_id, str(amount), source, date_))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'User: {user_id} deposited {amount} - source: {source}, date: {date_}')

        return self.cursor.lastrowid

    def get_deposit(self, id_: int) -> Deposit | None:
        # Attempt to fetch the deposit.
        self.cursor.execute('SELECT * FROM `deposits` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_deposit(row)

    def create_transaction(self, user_id: int, transaction_id: int, type_: str, date_: date) -> int:
        # Create the transaction report.
        self.cursor.execute('''
        INSERT INTO `transactions` (`user_id`, `transaction_id`, `type`, `date`)
        VALUES (?, ?, ?, ?)
        ''', (user_id, transaction_id, type_, date_))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Transaction created: user id: {user_id}, transaction id: {transaction_id}, type: {type_}, '
                    f'date: {date_}')

        return self.cursor.lastrowid

    def get_transaction(self, id_: int) -> Transaction | None:
        self.cursor.execute('SELECT * FROM `transactions` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_transaction(row)

    def get_transaction_for(self, transaction_id: int) -> Transaction | None:
        # Attempt to get a transaction for a specified transaction id (useful for reverse lookup on deposits and
        # purchases).
        self.cursor.execute('SELECT * FROM `transactions` WHERE `transaction_id` = ?', (transaction_id,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_transaction(row)

    def get_user_transactions(self, user_id: int) -> list[Transaction]:
        # Fetch all transactions of a specific user.
        self.cursor.execute('SELECT * FROM `transactions` WHERE `user_id` = ?', (user_id,))

        transactions: list[Transaction] = []

        for row in self.cursor.fetchall():
            transactions.append(Utils.row_to_transaction(row))

        return transactions

    def get_user_transactions_in(self, user_id: int, application_id: int) -> list[Transaction]:
        # Fetch all transactions of a specific user in a specific application.
        self.cursor.execute('SELECT * FROM `transactions` WHERE `user_id` = ? AND `application_id` = ?', (user_id, application_id))

        transactions: list[Transaction] = []

        for row in self.cursor.fetchall():
            transactions.append(Utils.row_to_transaction(row))

        return transactions

    def create_application_key(self, application_id: int, key: str, type_: str, redeemed: bool, user_id: int) -> tuple[bool, dict]:
        # Make sure the application key does not already exist.
        existing_key = self.get_application_key(key)

        if existing_key:
            return False, {'details': 'Application key already exists.'}

        # The key does not exist; create it.
        self.cursor.execute('''
        INSERT INTO `application_keys` (`application_id`, `key`, `type`, `redeemed`, `user_id`)
        VALUES (?, ?, ?, ?, ?)
        ''', (application_id, key, type_, redeemed, user_id))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Created application key for application: {application_id}, key: {key}, type: {type_}, '
                    f'redeemed: {redeemed}')

        return True, {'details': 'Application key created successfully.', 'key': key, 'id': self.cursor.lastrowid}

    def get_application_key(self, identifier, identifier_type: str = 'key') -> ApplicationKey | None:
        # Ensure that the identifier type is valid.
        if not identifier_type in ['id', 'key']:
            return None

        # Attempt to fetch the requested application key.
        self.cursor.execute(f'SELECT * FROM `application_keys` WHERE `{identifier_type}` = ? COLLATE NOCASE', (identifier,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_application_key(row)

    def delete_application_key(self, id_: int):
        # Attempt to delete the application key.
        self.cursor.execute('DELETE FROM `application_keys` WHERE `id` = ?', (id_,))

        # Commit the changes.
        self.connection.commit()

        logger.warning(f'Deleted application key: {id_}')

    def get_user_application_keys(self, user_id: int) -> list[ApplicationKey]:
        application_keys: list[ApplicationKey] = []

        # Fetch all application keys that belong to a user.
        self.cursor.execute('SELECT * FROM `application_keys` WHERE `user_id` = ?', (user_id,))

        # Loops through the keys.
        for row in self.cursor.fetchall():
            application_keys.append(Utils.row_to_application_key(row))

        return application_keys

    def get_application_key_for(self, user_id: int, application_id: int) -> ApplicationKey | None:
        # Attempt to get an application key from the specified user and application ids.
        self.cursor.execute('SELECT * FROM `application_keys` WHERE `user_id` = ? AND `application_id` = ?', (user_id, application_id))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_application_key(row)

    def create_friend_request(self, user_id: int, from_user_id: int) -> tuple[bool, dict]:
        # Ensure that there is not already a friend request matching this one, or from the opposite party.
        existing_request = self.get_friend_request_by_users(user_id, from_user_id)

        if existing_request:
            return False, {'details': 'Friend request already exists.'}

        # Ensure that the user is not sending a friend request to their self somehow.
        if user_id == from_user_id:
            return False, {'details': 'You cannot send a friend request to yourself.'}

        opposite_request = self.get_friend_request_by_users(from_user_id, user_id)

        if opposite_request:
            return False, {'details': 'There is already a friend request from the other person. You can accept that.'}

        # No friend request exists from either party to each other; send the friend request.
        self.cursor.execute('''
        INSERT INTO `friend_requests` (`user_id`, `from_user_id`, `date`)
        VALUES (?, ?, ?)
        ''', (from_user_id, user_id, date.today()))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'User {from_user_id} sent a friend request to user: {user_id}')

        return True, {'details': 'Friend request created successfully.', 'id': self.cursor.lastrowid}

    def get_friend_request_by_id(self, id_: int) -> FriendRequest | None:
        self.cursor.execute('SELECT * FROM `friend_requests` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_friend_request(row)

    def get_friend_request_by_users(self, user_id: int, from_user_id: int) -> FriendRequest | None:
        # Attempt to get a friend request sent by a certain user to a certain user. (It makes sense, trust me.)
        self.cursor.execute('''SELECT * FROM `friend_requests` WHERE `user_id` = ? AND `from_user_id` = ?''', (user_id, from_user_id))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_friend_request(row)

    def delete_friend_request(self, id_: int):
        # Attempt to delete the friend request.
        self.cursor.execute('DELETE FROM `friend_requests` WHERE `id` = ?', (id_,))

        # Commit the changes.
        self.connection.commit()

        logger.warning(f'Deleted friends request: {id_}')

    def accept_friend_request(self, id_: int) -> tuple[bool, dict]:
        # Fetch the friend request.
        request = self.get_friend_request_by_id(id_)

        if not request:
            return False, {'details': 'Friend request does not exist.'}

        # Accept the friend request.
        # Get the user ids from the friend request.
        user_id: int = request.user_id
        from_user_id: int = request.from_user_id

        # Get today's date.
        # (Multiple database entries will be made, and a very rare case could lead to the dates being
        # different without this.)
        today: date = date.today()

        # Add the friends into the database.

        # Query 1:
        self.cursor.execute('''
        INSERT INTO `friends` (`user_id`, `other_user_id`, `date`)
        VALUES (?, ?, ?)
        ''', (from_user_id, user_id, today))

        # Query 2:
        self.cursor.execute('''
        INSERT INTO `friends` (`user_id`, `other_user_id`, `date`)
        VALUES (?, ?, ?)
        ''', (from_user_id, user_id, today))

        # Commit the changes.
        self.connection.commit()

        # Delete the friend request.
        self.delete_friend_request(id_)

        logger.info(f'User {user_id} accepted a friend request from user: {from_user_id} - they are now friends.')

        return True, {'details': 'Friend request accepted successfully.'}

    def get_friends(self, user_id: int) -> list[Friend]:
        friends: list[Friend] = []

        # Get all friends of the specified user.
        self.cursor.execute('SELECT * FROM `friends` WHERE `user_id` = ?', (user_id,))

        # Loop through all the friends and add them to the list.
        rows = self.cursor.fetchall()

        for friend in rows:
            friends.append(Utils.row_to_friend(friend))

        return friends

    def get_friend_by_id(self, id_: int) -> Friend | None:
        # Attempt to get the friend entry from the provided id.
        self.cursor.execute('SELECT * FROM `friends` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_friend(row)

    def get_friend_by_users(self, user_id: int, from_user_id: int) -> Friend | None:
        # Attempt to get a friend entry based on two user ids. (Useful for verifying that two users are friends.)
        self.cursor.execute('SELECT * FROM `friends` WHERE `user_id` = ? AND `other_user_id` = ?', (user_id, from_user_id))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_friend(row)

    def are_friends(self, user_id: int, from_user_id: int) -> bool:
        # Check if two users are friends.
        return self.get_friend_by_users(user_id, from_user_id) is not None

    def remove_friend(self, user_id: int, other_user_id: int) -> tuple[bool, dict]:
        # Check if the two users are friends in the first place.
        if not self.are_friends(user_id, other_user_id):
            return False, {'details': 'You are not friends with that user.'}

        # The users are friends; delete the entries.
        # Entry 1:
        self.cursor.execute('DELETE FROM `friends` WHERE `user_id` = ? AND `other_user_id` = ?', (user_id, other_user_id))

        # Entry 2:
        self.cursor.execute('DELETE FROM `friends` WHERE `user_id` = ? AND `other_user_id` = ?', (other_user_id, user_id))

        # Commit the changes.
        self.connection.commit()

        logger.warning(f'User: {user_id} removed user: {other_user_id} as a friend. They are no long friends.')

        return True, {'details': 'Friend removed successfully.'}

    def create_session(self, user_id: int, hostname: str, mac_address: str, platform: str, start_date: date,
                       last_activity: date) -> tuple[bool, dict]:
        # Create a new session with the provided information.
        # Generate a session id.
        session_id: str = Utils.generate_session_identifier()

        self.cursor.execute('''
        INSERT INTO `sessions` (`identifier`, `user_id`, `hostname`, `mac_address`, `platform`, `start_date`, `last_activity`)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, hostname, mac_address, platform, start_date, last_activity))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Created session {session_id} for user: {user_id} - hostname: {hostname}, '
                    f'mac_address: {mac_address}, platform: {platform}')

        return True, {'details': 'Session created successfully.', 'session_id': session_id}

    def get_session(self, identifier, identifier_type: str = 'identifier') -> Session | None:
        # Ensure that the identifier type is valid.
        if not identifier_type in ['id', 'identifier']:
            return None

        # Attempt to get the session
        self.cursor.execute(f'SELECT * FROM `sessions` WHERE `{identifier_type}` = ?', (identifier,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_session(row)

    def delete_session(self, id_: int):
        # Delete the session.
        self.cursor.execute('DELETE FROM `sessions` WHERE `id` = ?', (id_,))

        # Commit the changes.
        self.connection.commit()

        logger.warning(f'Deleted session: {id_}')

    def update_session_last_activity(self, id_: int, date_: date):
        # Update the session.
        self.cursor.execute('UPDATE `sessions` SET `last_activity` = ? WHERE `id` = ?', (date_, id_))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Updated session: {id_} - last activity: {date_}')

    def get_sessions_for(self, user_id: int) -> list[Session]:
        sessions: list[Session] = []

        # Get all the specified user's sessions.
        self.cursor.execute('SELECT * FROM `sessions` WHERE `user_id` = ?', (user_id,))

        # Loop through all of them, and add them to the list.
        for session in self.cursor.fetchall():
            sessions.append(Utils.row_to_session(session))

        return sessions

    def create_invite(self, user_id: int, from_user_id: int, application_id: int, details: dict,
                      date_: date):
        # Create the invite.
        self.cursor.execute('''
        INSERT INTO `invites` (`user_id`, `from_user_id`, `application_id`, `details`, `date`)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, from_user_id, application_id, json.dumps(details), date_))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'User: {user_id} invited user: {from_user_id} - application: {application_id}, details: {details}')

    def get_invite_by_id(self, id_: int) -> Invite | None:
        # Attempt to get the requested invite.
        self.cursor.execute('SELECT * FROM `invites` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_invite(row)

    def get_user_invites(self, user_id: int) -> list[Invite]:
        invites: list[Invite] = []

        # Get all the invites for a specific user.
        self.cursor.execute('SELECT * FROM `invites` WHERE `user_id` = ?', (user_id,))

        # Loop through all the invites.
        for invite in self.cursor.fetchall():
            invites.append(Utils.row_to_invite(invite))

        return invites

    def get_user_invites_for(self, user_id: int, application_id: int) -> list[Invite]:
        invites: list[Invite] = []

        # Get all invites for a user in a specific application.
        self.cursor.execute('SELECT * FROM `invites` WHERE `user_id` = ? AND `application_id` = ?', (user_id, application_id))

        # Loop through all the invites.
        for invite in self.cursor.fetchall():
            invites.append(Utils.row_to_invite(invite))

        return invites

    def delete_invite(self, id_: int):
        # Attempt to delete the specified invite.
        self.cursor.execute('DELETE FROM `invites` WHERE `id` = ?', (id_,))

        # Commit the changes.
        self.connection.commit()

        logger.warning(f'Deleted invite: {id_}')

    def create_application_session(self, user_id: int, application_id: int, date_: date,
                                   length: int):
        # Create the session.
        self.cursor.execute('''
        INSERT INTO `application_sessions` (`user_id`, `application_id`, `date`, `length`)
        VALUES (?, ?, ?, ?)
        ''', (user_id, application_id, date_, length))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'{user_id} had a {length} session in {application_id} - date: {date_}')

    def get_application_session(self, id_: int) -> ApplicationSession | None:
        # Attempt to get the application session.
        self.cursor.execute('SELECT * FROM `application_sessions` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_application_session(row)

    def get_user_application_sessions(self, user_id: int, application_id: int = -1) -> list[ApplicationSession]:
        sessions: list[ApplicationSession] = []

        if application_id == -1:
            self.cursor.execute('SELECT * FROM `application_sessions` WHERE `user_id` = ?', (user_id,))
        else:
            self.cursor.execute('SELECT * FROM `application_sessions` WHERE `user_id` = ? AND `application_id` = ?', (user_id, application_id))

        for row in self.cursor.fetchall():
            sessions.append(Utils.row_to_application_session(row))

        return sessions

    def get_application_sessions(self, application_id: int = -1) -> list[ApplicationSession]:
        sessions: list[ApplicationSession] = []

        if application_id == -1:
            self.cursor.execute('SELECT * FROM `application_sessions`')
        else:
            self.cursor.execute('SELECT * FROM `application_sessions` WHERE `application_id` = ?', (application_id,))

        for row in self.cursor.fetchall():
            sessions.append(Utils.row_to_application_session(row))

        return sessions

    def create_photo(self, filename: str, subfolder: str, created_at: date) -> tuple[bool, dict]:
        # Ensure that there is not already a photo in the database stored at the same location.
        existing_photo = self.get_photo_by_location(filename, subfolder)

        if existing_photo:
            return False, {'details': 'A photo with this name and path already exists.'}

        # Insert the photo into the database.
        self.cursor.execute('''
        INSERT INTO `photos` (`filename`, `subfolder`, `created_at`)
        VALUES (?, ?, ?)
        ''', (filename, subfolder, created_at))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Created photo entry: {filename} - subfolder: {subfolder}')

        return True, {'details': 'Photo created successfully.'}

    def get_photo_by_id(self, id_: int) -> Photo | None:
        # Attempt to get a photo from the provided id.
        self.cursor.execute('SELECT * FROM `photos` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_photo(row)

    def get_photo_by_location(self, filename: str, subfolder: str) -> Photo | None:
        # Attempt to get a photo based on a filename a subfolder.
        self.cursor.execute('SELECT * FROM `photos` WHERE `filename` = ? AND `subfolder` = ?', (filename, subfolder))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_photo(row)

    def create_iap(self, application_id: int, title: str, description: str, price: float,
                   data: dict) -> tuple[bool, dict]:
        # Create the in-app-purchase (iap).
        self.cursor.execute('''
        INSERT INTO `iaps` (`application_id`, `title`, `description`, `price`, `data`)
        VALUES (?, ?, ?, ?, ?)
        ''', (application_id, title, description, str(price), json.dumps(data)))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Created iap: {title} - description: {description} for application: {application_id}, '
                    f'price: {price}, data: {data}')

        return True, {'details': 'IAP created successfully.', 'id': self.cursor.lastrowid}

    def get_iap(self, id_: int) -> IAP | None:
        # Get a specific iap (from an id).
        self.cursor.execute('SELECT * FROM `iaps` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_iap(row)

    def get_iaps_for_application(self, application_id: int) -> list[IAP]:
        # Gather all iaps for a specific application.
        iaps: list[IAP] = []

        self.cursor.execute('SELECT * FROM `iaps` WHERE `application_id` = ?', (application_id,))

        for row in self.cursor.fetchall():
            iaps.append(Utils.row_to_iap(row))

        return iaps

    def create_cloud_data(self, user_id: int, application_id: int, data: dict):
        # Delete all previous cloud data entries for that user and application id.
        self.cursor.execute('DELETE FROM `cloud_data` WHERE `user_id` = ? AND `application_id` = ?', (user_id, application_id))

        # Save the data.
        self.cursor.execute('''
        INSERT INTO `cloud_data` (`user_id`, `application_id`, `data`, `date`)
        VALUES (?, ?, ?, ?)
        ''', (user_id, application_id, json.dumps(data), date.today()))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Created cloud data for user: {user_id} - application: {application_id}, data: {data}')

    def get_cloud_data(self, user_id: int, application_id: int) -> CloudData | None:
        self.cursor.execute('SELECT * FROM `cloud_data` WHERE `user_id` = ? AND `application_id` = ?', (user_id, application_id))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_cloud_data(row)

    def delete_cloud_data(self, user_id: int, application_id: int):
        # Delete the user's cloud data for the specified application.
        self.cursor.execute('DELETE FROM `cloud_data` WHERE `user_id` = ? AND `application_id` = ?', (user_id, application_id))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Deleted cloud data for user: {user_id} - application: {application_id}')

    def delete_application_cloud_data(self, application_id: int):
        # Delete all the cloud data for the specified application.
        self.cursor.execute('DELETE FROM `cloud_data` WHERE `application_id` = ?', (application_id,))

        # Commit the changes.
        self.connection.commit()

        logger.info(f'Deleted cloud data for application: {application_id}')

    def create_iap_record(self, iap_id: int, user_id: int, date_: date,
                          acknowledged: bool = False) -> tuple[bool, dict]:
        # Ensure that the iap exists.
        iap = self.get_iap(iap_id)

        if iap is None:
            return False, {'details': 'IAP not found.'}

        # Ensure that the user exists.
        user = self.get_user(user_id)

        if user is None:
            return False, {'details': 'User not found.'}

        # Everything is okay; create the iap record.
        self.cursor.execute('''
        INSERT INTO `iap_records` (`iap_id`, `user_id`, `date`, `acknowledged`)
        VALUES (?, ?, ?, ?)
        ''', (iap_id, user_id, date_, acknowledged))

        return True, {'details': 'IAP record created successfully.', 'id': self.cursor.lastrowid}

    def get_iap_records(self, application_id: int, user_id: int, only_unacknowledged: bool = False) -> list[IAPRecord]:
        # Fetch the iap records for a specific user, in a specific application.
        # Ensure that the application exists.
        application = self.get_application(application_id)

        if application is None:
            return []

        # Ensure that the user exists.
        user = self.get_user(user_id)

        if user is None:
            return []

        records: list[IAPRecord] = []

        # Get the records.
        if only_unacknowledged:
            self.cursor.execute('SELECT * FROM `iap_records` WHERE `application_id` = ? AND `user_id` = ? and `acknowledged` = ?', (application_id, user_id, False))
        else:
            self.cursor.execute('SELECT * FROM `iap_records` WHERE `application_id` = ? AND `user_id` = ?', (application_id, user_id))

        # Loop through all the records, adding them to the list.
        for row in self.cursor.fetchall():
            records.append(Utils.row_to_iap_record(row))

        return records

    def get_iap_record(self, id_: int) -> IAPRecord | None:
        # Attempt to get the iap record.
        self.cursor.execute('SELECT * FROM `iap_records` WHERE `id` = ?', (id_,))
        row = self.cursor.fetchone()

        if row is None:
            return None

        return Utils.row_to_iap_record(row)

    def acknowledge_iap_record(self, id_: int) -> tuple[bool, dict]:
        # Ensure that the iap record exists.
        iap_record = self.get_iap_record(id_)

        if iap_record is None:
            return False, {'details': 'IAP record not found.'}

        if iap_record.acknowledged:
            return False, {'details': 'IAP record already acknowledged.'}

        # Update the record.
        self.cursor.execute('UPDATE `iap_records` SET `acknowledged = ? WHERE `id` = ?', (True, id_))

        return True, {'details': 'IAP record acknowledged successfully.'}
