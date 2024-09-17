import json
import os
import sys

from dotenv import load_dotenv
from datetime import datetime
from datetime import date
from loguru import logger

# Flask-related imports.
from flask import Flask, request, send_file
from flask_restful import Api
from werkzeug.utils import secure_filename

# Local imports.
from database import Database
from database_utils import DatabaseUtils
from email_manager import EmailManager
from api_resource import APIResource
from file_manager import FileManager
from structures.application_session import ApplicationSession
from structures.iap_record import IAPRecord
from structures.application_key import ApplicationKey
from structures.application_version import ApplicationVersion
from structures.sale import Sale
from structures.transaction import Transaction
from structures.user import User
from utils import Utils


# Constants.
BASE_DIRECTORY: str = 'data'
PHOTOS_DIRECTORY: str = 'photos'
APPLICATIONS_DIRECTORY: str = 'applications'
ALLOWED_IMAGE_TYPES: list = ['png', 'jpg', 'jpeg']


# Variables.
email_manager: EmailManager | None = None
database: Database | None = None
database_utils: DatabaseUtils | None = None
file_manager: FileManager | None = None
app = None
api = None


# Api classes.
class Ping(APIResource):
    @staticmethod
    def get():
        return {'ping': 'pong'}


class RequestEmailVerification(APIResource):
    required_parameters = ['email_address']

    def post(self):
        # Ensure that there are no missing parameters.
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        # Get the email address from the form data.
        email_address: str = request.form.get('email_address')

        # Request a verification code from the database.
        database.request_email_verification_code(email_address)

        return {}, 200


class CheckEmailVerification(APIResource):
    required_parameters = ['email_address', 'verification_code']

    def post(self):
        # Ensure that there are no missing parameters.
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        # Get the parameters.
        email_address: str = request.form.get('email_address')
        verification_code: int = Utils.safe_int_cast(request.form.get('verification_code'))

        # Check the provided code against the database.
        email_verified: bool = database.check_email_verification(email_address, verification_code)

        return {'email_verified': email_verified}, 200


class Register(APIResource):
    required_parameters = ['username', 'name', 'email_address', 'password', 'email_verification_code']

    def post(self):
        # Ensure that there are no missing parameters.
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        # Get the parameters.
        username: str = request.form.get('username')
        name: str = request.form.get('name')
        email_address: str = request.form.get('email_address')
        password: str = request.form.get('password')
        email_verification_code: int = Utils.safe_int_cast(request.form.get('email_verification_code'))

        # Attempt to register the user.
        success, response = database.create_user(username, name, email_address, password, email_verification_code)

        if success:
            return response
        else:
            return response, 400


class Login(APIResource):
    required_parameters = ['username', 'password', 'hostname', 'mac_address',
                           'platform'] # Session-related parameters are also required.

    def post(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        # Get the parameters.
        username: str = request.form.get('username')
        password: str = request.form.get('password') # The provided password, not hashed.
        hostname: str = request.form.get('hostname')
        mac_address: str = request.form.get('mac_address')
        platform: str = request.form.get('platform')

        # Attempt to fetch the user based on the provided username.
        user: User | None = database.get_user(username, 'username')

        if not user:
            return {'details': 'A user with the specified username does not exist.'}, 400

        # The user exists; check the password.
        # Get the password.
        user_password: str = user.password # The user's hashed password, retrieved from the database.

        # Check the provided password against the one from the database.
        if not Utils.password_matches(password, user_password):
            return {'details': 'Password does not match.'}, 400

        # The password matched, attempt to create the session.
        success, response = (
            database.create_session(user.id, hostname, mac_address, platform, date.today(), date.today()))

        if not success:
            return {'details': 'Failed to create session.', 'additional_data': response}, 400

        # The session was successfully created.
        # Get the session id.
        session_id: str = response['session_id']

        return {'session_id': session_id}, 200


class GetUser(APIResource):
    required_parameters = ['user_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the user.
        session_user = database.get_user(session.user_id)

        # Get the parameters.
        user_id: int = Utils.safe_int_cast(request.form.get('user_id'))

        # Get the requested user.
        user = database.get_user(user_id)

        if not user:
            return {'details': 'The specified user does not exist.'}, 400

        return user.into_dict(user.is_or_admin(session_user.id)), 200


class AuthenticateSession(APIResource):
    required_parameters = []

    def get(self):
        # Ensure that the client is authenticated with the session id they would like to check.
        authenticated, session_id = self.get_authentication()

        if not authenticated:
            return {}, 401

        # The user is authenticated. Now, validate their session id.
        session = database.get_session(session_id)

        if not session:
            return {'authenticated': False}

        # The user's session is valid. Update the session's last activity date to prevent it from being deleted.
        database.update_session_last_activity(session.id, date.today())

        return {'authenticated': True, 'user_id': session.user_id}, 200


class DeleteSession(APIResource):
    def delete(self):
        # Ensure that the client is authenticated with the session id they would like to check.
        authenticated, session_id = self.get_authentication()

        if not authenticated:
            return {}, 401

        # The user is authenticated. Now, get their session id.
        session = database.get_session(session_id)

        if not session:
            return {'details': 'The specified session does not exist.'}, 400

        database.delete_session(session.id)

        return {}


class CreateApplication(APIResource):
    required_parameters = ['name', 'package_name', 'type', 'description', 'release_date', 'early_access',
                           'supported_platforms', 'genres', 'tags', 'base_price']

    def post(self):
        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Ensure that the user has developer permissions.
        if not user:
            return {'details': 'The session\'s user does not exist.'}, 400

        if not user.has_developer_permissions():
            return {'details': 'You are not a developer!'}, 403

        # Get the parameters.
        name: str = request.form.get('name')
        package_name: str = request.form.get('package_name')
        type_: str = request.form.get('type')
        description: str = request.form.get('description')
        release_date: date = datetime.strptime(request.form.get('release_date'), '%Y-%m-%d').date()
        early_access: bool = Utils.safe_bool_cast(request.form.get('early_access'))
        latest_version: str = '' # Empty, signifying that there is no version available (at this time).
        supported_platforms: list = request.form.get('supported_platforms').split(',')
        genres: list = request.form.get('genres').split(',')
        tags: list = request.form.get('tags').split(',')
        base_price: float = Utils.safe_float_cast(request.form.get('base_price'))
        owners: list = [str(user.id)]

        # Attempt to create the application.
        success, response = database.create_application(
            name,
            package_name,
            type_,
            description,
            release_date,
            early_access,
            latest_version,
            supported_platforms,
            genres,
            tags,
            base_price,
            owners
        )

        # Create the application's data folder (for storing versions).
        file_manager.create_application_folder(package_name)

        if not success:
            return response, 400

        return {'details': 'Successfully created application.', 'application_id': response['application_id']}, 200


class GetApplication(APIResource):
    required_parameters = ['application_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))

        # Get the application.
        application = database.get_application(application_id)

        if not application:
            return {'details': 'The specified application does not exist.'}, 400

        return application.into_dict(user.administrator or user.id in application.owners), 200


class UpdateApplicationVersion(APIResource):
    required_parameters = ['application_id', 'version']

    def put(self):
        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Ensure that the user has developer permissions.
        if not user.has_developer_permissions():
            return {'details': 'You are not a developer!'}, 403

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))
        version: str = request.form.get('version')

        # Ensure that the application exists.
        # Get the application.
        application = database.get_application(application_id)

        if not application:
            return {'details': 'The specified application does not exist.'}, 400

        # Ensure that the user is an owner of this application.
        if not user.id in application.owners:
            return {'details': 'This is not your application; you cannot update its version.'}, 403

        database.update_application_property(application_id, 'latest_version', version)

        return {}


class GetApplicationVersions(APIResource):
    required_parameters = ['application_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))

        # Verify that the user owns the specified application.
        if not database_utils.user_owns(user.id, application_id):
            return {'details': 'You do not own this application.'}

        versions: list[ApplicationVersion]

        if 'platform' in request.form:
            versions = database.get_application_versions_for_platform(application_id, str(request.form.get('platform')))
        else:
            versions = database.get_application_versions(application_id)

        return {'versions': Utils.serialize(versions)}, 200


class DownloadApplicationVersion(APIResource):
    required_parameters = ['version_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        version_id: int = Utils.safe_int_cast(request.form.get('version_id'))

        # Get the version.
        version = database.get_application_version_by_id(version_id)

        if not version:
            return {'details': 'The specified version does not exist.'}, 400

        # Verify that the user owns the specified application.
        if not database_utils.user_owns(user.id, version.application_id):
            return {'details': 'You do not own this application.'}, 403

        return send_file(file_manager.get_version_filepath(version_id))


class CreateVersion(APIResource):
    required_parameters = ['application_id', 'name', 'platform', 'release_date', 'filename', 'executable']
    required_files = ['file']

    def post(self):
        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        if not user.has_developer_permissions():
            return {'details': 'You are not a developer!'}, 403

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))
        name: str = request.form.get('name')
        platform: str = request.form.get('platform')
        release_date: date = datetime.strptime(request.form.get('release_date'), '%Y-%m-%d').date()
        filename: str = Utils.generate_uuid4() + '_' + request.form.get('filename')
        executable = request.form.get('executable')

        # Ensure that the application exists.
        # Get the application.
        application = database.get_application(application_id)

        if not application:
            return {'details': 'The specified application does not exist.'}, 400

        # Ensure that the user is an owner of this application.
        if not user.id in application.owners:
            return {'details': 'This is not your application; you cannot push versions to it.'}, 403

        # Everything is good; create the version.
        # Ensure that a file was provided.
        missing_files, missing_files_list = self.missing_files()

        if missing_files:
            return {'details': 'Please provide a version file.'}, 400

        # Create the version entry in the database first to make sure there is not an issue.
        success, response = database.create_application_version(
            application_id,
            name,
            platform,
            release_date,
            filename,
            executable
        )

        # Handle errors.
        if not success:
            return response, 400

        # No issues creating the version; upload the file.
        # Get the version file.
        version_file = request.files['file']

        # Save the version file.
        version_file.save(file_manager.generate_version_filepath(application.package_name, secure_filename(filename)))

        return response, 200


class GetVersion(APIResource):
    required_parameters = ['application_id', 'version_name', 'platform']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))
        version_name: str = request.form.get('version_name')
        platform: str = request.form.get('platform')

        # Verify that the user owns the specified application.
        if not database_utils.user_owns(user.id, application_id):
            return {'details': 'You do not own this application.'}, 403

        # Get the version.
        version = database.get_application_version(application_id, version_name, platform)

        if not version:
            return {'details': 'The specified version does not exist.'}, 400

        # Get the application.
        application = database.get_application(application_id)

        return version.into_dict(user.administrator or user.id in application.owners), 200


class CreateSale(APIResource):
    required_parameters = ['application_id', 'title', 'description', 'price', 'start_date', 'end_date']

    def post(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        if not user.has_developer_permissions():
            return {'details': 'You are not a developer!'}, 403

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))
        title: str = request.form.get('title')
        description: str = request.form.get('description')
        price: float = Utils.safe_float_cast(request.form.get('price'))
        start_date: date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date: date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()

        # Ensure that the application exists.
        # Get the application.
        application = database.get_application(application_id)

        if not application:
            return {'details': 'The specified application does not exist.'}, 400

        # Ensure that the user is an owner of this application.
        if not user.id in application.owners:
            return {'details': 'This is not your application; you cannot create sales for it.'}, 403

        success, response = database.create_sale(application_id, title, description, price, start_date, end_date)

        if success:
            return response, 200

        return response, 400


class GetActiveSale(APIResource):
    required_parameters = ['application_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))

        # Ensure that the application exists.
        application = database.get_application(application_id)

        if not application:
            return {'details': 'The specified application does not exist.'}, 400

        # Attempt to find the active sale of a specific application.
        sale = database.get_active_sale(application_id, date.today())

        if not sale:
            return {'details': 'The specified application is not currently on sale.'}, 400

        return sale.into_dict(), 200


class GetAllActiveSales(APIResource):
    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        sales: list[Sale] = []

        # Loop through all applications.
        for application in database.get_all_applications():
            # Attempt to grab the currently active sale for the application (if any).
            active_sale = database.get_active_sale(application.id, date.today())

            # If there is an active sale, add it to the list.
            if active_sale:
                sales.append(active_sale)

        return {'sales': Utils.serialize(sales)}, 200


class DeleteSale(APIResource):
    required_parameters = ['sale_id']

    def delete(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        if not user.has_developer_permissions():
            return {'details': 'You are not a developer!'}, 403

        # Get the parameters.
        sale_id: int = Utils.safe_int_cast(request.form.get('sale_id'))

        # Ensure that the sale exists.
        # Get the sale.
        sale = database.get_sale(sale_id)

        if not sale:
            return {'details': 'The specified sale does not exist.'}, 400

        # Get the application.
        application = database.get_application(sale.application_id)

        # Ensure that the user is an owner of this application.
        if not user.id in application.owners:
            return {'details': 'This is not your application; you cannot create sales for it.'}, 403

        # Delete the sale.
        success, response = database.delete_sale(sale_id)

        if success:
            return response, 200

        return response, 400


class GetTransactions(APIResource):
    required_parameters = ['user_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        user_id: int = Utils.safe_int_cast(request.form.get('user_id'))

        # Ensure that the user exists.
        target_user = database.get_user(user_id)

        if not target_user:
            return {'details': 'The specified user does not exist.'}, 400

        # Ensure that the user requesting to fetch the transactions has the proper authority to do so.
        if not user.is_or_admin(user_id):
            return {'details': 'You do not have the authority to access this user\'s transaction records.'}, 403

        transactions: list[Transaction] = []

        # Get the user's transactions.
        if 'application_id' in request.form:
            transactions = database.get_user_transactions_in(user_id,
                                                             Utils.safe_int_cast(request.form.get('application_id')))
        else:
            transactions = database.get_user_transactions(user_id)

        return {'transactions': Utils.serialize(transactions, True)}, 200


class GetTransaction(APIResource):
    required_parameters = ['transaction_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        transaction_id: int = Utils.safe_int_cast(request.form.get('transaction_id'))

        # Ensure that the transaction exists.
        transaction = database.get_transaction(transaction_id)

        if not transaction:
            return {'details': 'The specified transaction does not exist.'}, 400

        # Ensure that the user requesting the transaction has the proper authority to view it.
        if not user.is_or_admin(transaction.user_id):
            return {'details': 'You do not have the authority to access this user\'s transaction(s).'}, 403

        return {'transaction': Utils.serialize(transaction, True)}, 200


class GetPurchase(APIResource):
    required_parameters = ['purchase_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters
        purchase_id: int = Utils.safe_int_cast(request.form.get('purchase_id'))

        # Ensure that the purchase exists.
        purchase = database.get_purchase(purchase_id)

        if not purchase:
            return {'details': 'The specified purchase does not exist.'}, 400

        # Ensure that the user has the proper authority to access this purchase.
        if not user.is_or_admin(database_utils.get_purchase_source(purchase_id)):
            return {'details': 'You do not have the authority to access this user\'s purchase(s).'}, 403

        return {'purchase': Utils.serialize(purchase, True)}, 200


class GetDeposit(APIResource):
    required_parameters = ['deposit_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        deposit_id: int = Utils.safe_int_cast(request.form.get('deposit_id'))

        # Ensure that the deposit exists.
        deposit = database.get_deposit(deposit_id)

        if not deposit:
            return {'details': 'The specified deposit does not exist.'}, 400

        # Ensure that the user has the authority to view the requested deposit.
        if not user.is_or_admin(deposit.user_id):
            return {'details': 'You do not have the authority to access this user\'s deposit(s).'}, 403

        return {'deposit': Utils.serialize(deposit, True)}, 200


class GetApplicationKey(APIResource):
    required_parameters = ['key']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        key = request.form.get('key')

        # Attempt to get the application key.
        application_key = database.get_application_key(key)

        if not application_key:
            return {'details': 'The specified application key does not exist.'}, 400

        # Ensure the user has the authority to access this application key.
        if not user.is_or_admin(application_key.user_id):
            return {'details': 'You do not have the authority to access this user\'s application key(s).'}, 403

        return {'application_key': Utils.serialize(application_key, True)}, 200


class GetApplicationKeys(APIResource):
    required_parameters = ['user_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        user_id: int = Utils.safe_int_cast(request.form.get('user_id'))

        # Ensure that the user exists.
        target_user = database.get_user(user_id)

        if not target_user:
            return {'details': 'The specified user does not exist.'}, 400

        # Ensure that the user has authority to access the authentication keys.
        if not user.is_or_admin(user_id):
            return {'details': 'You do not have the authority to access this user\'s application key(s).'}, 403

        # Get the authentication keys.
        application_keys: list[ApplicationKey] = database.get_user_application_keys(user_id)

        return {'application_keys': Utils.serialize(application_keys, True)}, 200


class PurchaseApplication(APIResource):
    required_parameters = ['application_id']

    def post(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))

        # Ensure that the application exists.
        application = database.get_application(application_id)

        if not application:
            return {'details': 'The specified application does not exist.'}, 400

        # Get the optional parameters.
        for_user_id: int = Utils.safe_int_cast(request.form.get('for_user_id')) \
            if 'for_user_id' in request.form \
            else user.id

        # Attempt to purchase the application.
        success, response = database_utils.purchase(user.id, application_id, for_user_id)

        if not success:
            return response, 400

        return {'details': 'Successfully purchased application.', 'transaction_id': response['transaction_id']}, 200


class PurchaseIAP(APIResource):
    required_parameters = ['iap_id']

    def post(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        iap_id: int = Utils.safe_int_cast(request.form.get('iap_id'))

        # Ensure that the iap exists.
        iap = database.get_iap(iap_id)

        if not iap:
            return {'details': 'The specified iap does not exist.'}, 400

        # Get the optional parameters.
        for_user_id: int = Utils.safe_int_cast(request.form.get('for_user_id')) \
            if 'for_user_id' in request.form \
            else user.id

        success, response = database_utils.purchase(user.id, iap_id, for_user_id, iap_id)

        if not success:
            return response, 400

        return {'details': 'Successfully purchased iap.', 'transaction_id': response['transaction_id']}, 200


class GetIAPRecords(APIResource):
    required_parameters = ['user_id', 'application_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        user_id: int = Utils.safe_int_cast(request.form.get('user_id'))
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))

        # Ensure that the user exists.
        target_user = database.get_user(user_id)

        if not target_user:
            return {'details': 'The specified user does not exist.'}, 400

        # Ensure that the user has the authority to view this user's iap records.
        if not user.is_or_admin(target_user.id):
            return {'details': 'You do not have the authority to access this user\'s iap records(s).'}, 403

        # Get the iap records.
        records: list[IAPRecord] = database.get_iap_records(user_id, application_id)

        return {'iap_records': Utils.serialize(records, True)}, 200


class GetSession(APIResource):
    required_parameters = ['session_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        session_id: str = request.form.get('session_id')

        # Ensure that the session exists.
        session = database.get_session(session_id)

        if not session:
            return {'details': 'The specified session does not exist.'}, 400

        # Ensure that the user has the authority to view this session.
        if not user.is_or_admin(session.user_id):
            return {'details': 'You do not have the authority to access this session.'}, 403

        return Utils.serialize(session, True), 200


class SendFriendRequest(APIResource):
    required_parameters = ['user_id']

    def post(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        user_id: int = Utils.safe_int_cast(request.form.get('user_id'))

        # Ensure that the other user exists.
        other_user = database.get_user(user_id)

        if not other_user:
            return {'details': 'The specified user does not exist.'}, 400

        # Ensure that the two users are not already friends.
        if database.are_friends(user.id, user_id):
            return {'details': 'You are already friends.'}, 400

        # Send the friend request.
        success, response = database.create_friend_request(user_id, user.id)

        if not success:
            return response, 400

        return response, 200


class DeleteFriendRequest(APIResource):
    required_parameters = ['request_id']

    def delete(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        request_id: int = Utils.safe_int_cast(request.form.get('request_id'))

        # Ensure that the friend request exists.
        friend_request = database.get_friend_request_by_id(request_id)

        if not friend_request:
            return {'details': 'The specified friend request does not exist.'}, 400

        # Ensure that the user has the authority to delete the friend request.
        if not (friend_request.user_id == user.id or friend_request.from_user_id == user.id or user.administrator):
            return {'details': 'You cannot delete this friend request.'}, 400

        return {}, 200


class AcceptFriendRequest(APIResource):
    required_parameters = ['request_id']

    def post(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        request_id: int = Utils.safe_int_cast(request.form.get('request_id'))

        # Ensure that the friend request exists.
        friend_request = database.get_friend_request_by_id(request_id)

        if not friend_request:
            return {'details': 'The specified friend request does not exist.'}, 400

        # Ensure that the user has the authority to accept the friend request (they aren't the one who sent it).
        if not friend_request.user_id == user.id:
            return {'details': 'You cannot accept this friend request.'}, 400

        # Accept the friend request.
        success, response = database.accept_friend_request(request_id)

        if not success:
            return response, 400

        return response, 200


class RemoveFriend(APIResource):
    required_parameters = ['user_id']

    def delete(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        user_id: int = Utils.safe_int_cast(request.form.get('user_id'))

        # Ensure that the user exists.
        target_user = database.get_user(user_id)

        if not target_user:
            return {'details': 'The specified user does not exist.'}, 400

        # Ensure that the two users are actually friends.
        if not database.are_friends(user.id, user_id):
            return {'details': 'You are not friends with this user.'}, 400

        # Remove the user as a friend.
        success, response = database.remove_friend(user.id, user_id)

        if not success:
            return response, 400

        return response, 200


class DeleteSpecificSession(APIResource):
    required_parameters = ['session_id']

    def delete(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        session_id: int = Utils.safe_int_cast(request.form.get('session_id'))

        # Ensure that the session exists.
        target_session = database.get_session(session_id, 'id')

        if not target_session:
            return {'details': 'The specified session does not exist.'}, 400

        # Ensure that the user has the authority to delete this session.
        if not user.is_or_admin(target_session.user_id):
            return {'details': 'You do not have the authority to delete this session.'}, 403

        # Delete the session.
        database.delete_session(session_id)

        return {}, 200


class SendInvite(APIResource):
    required_parameters = ['user_id', 'application_id', 'details']

    def post(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        user_id: int = Utils.safe_int_cast(request.form.get('user_id'))
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))
        details: dict = json.loads(request.form.get('details'))

        # Send the invite.
        database.create_invite(user_id, user.id, application_id, details, date.today())

        return {}, 200


class GetInvites(APIResource):
    required_parameters = ['user_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        user_id: int = Utils.safe_int_cast(request.form.get('user_id'))

        # Ensure that the user exists.
        target_user = database.get_user(user_id)

        if not target_user:
            return {'details': 'The specified user does not exist.'}, 400

        # Ensure that the user has the authority to view the invites.
        if not user.is_or_admin(user_id):
            return {'details': 'You do not have the authority to access this user\'s invites.'}, 403

        # Get the optional parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id')) if 'application_id' in request.form else -1

        # Get the invites.
        invites = database.get_user_invites(user_id) if application_id == -1 else database.get_user_invites_for(user_id, application_id)

        return {'invites': Utils.serialize(invites, True)}, 200


class GetInvite(APIResource):
    required_parameters = ['invite_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        invite_id: int = Utils.safe_int_cast(request.form.get('invite_id'))

        # Ensure that the invite exists.
        invite = database.get_invite_by_id(invite_id)

        if not invite:
            return {'details': 'The specified invite does not exist.'}, 400

        # Ensure that the user has the authority to access this invite.
        if not user.is_or_admin(invite.user_id):
            return {'details': 'You do not have the authority to access this invite.'}, 403

        return Utils.serialize(invite, True)


class DeleteInvite(APIResource):
    required_parameters = ['invite_id']

    def delete(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        invite_id: int = Utils.safe_int_cast(request.form.get('invite_id'))

        # Ensure that the invite exists.
        invite = database.get_invite_by_id(invite_id)

        if not invite:
            return {'details': 'The specified invite does not exist.'}, 400

        # Ensure that the user has the authority to delete this invite.
        if not user.is_or_admin(invite.user_id):
            return {'details': 'You do not have the authority to delete this invite.'}, 403

        # Delete the invite.
        database.delete_invite(invite_id)

        return {}, 200


class CreateApplicationSession(APIResource):
    required_parameters = ['application_id', 'length']

    def post(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))
        length: int = Utils.safe_int_cast(request.form.get('length'))

        # Create the application session.
        database.create_application_session(
            user.id,
            application_id,
            date.today(),
            length
        )

        return {}, 200


class GetApplicationSession(APIResource):
    required_parameters = ['id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        id_: int = Utils.safe_int_cast(request.form.get('id'))

        # Ensure that the application session exists.
        application_session = database.get_application_session(id_)

        if not application_session:
            return {'details': 'The specified application session does not exist.'}, 400

        # Ensure that the user has the authority to access this application session.
        if not user.is_or_admin(application_session.user_id):
            return {'details': 'You do not have the authority to access this application session.'}, 403

        return Utils.serialize(application_session, True)


class GetUserApplicationSessions(APIResource):
    required_parameters = ['user_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        user_id: int = Utils.safe_int_cast(request.form.get('user_id'))

        # Ensure that the user has the authority to get the application sessions.
        if not user.is_or_admin(user_id):
            return {'details': 'You do not have the authority to access this user\'s application session(s).'}, 403

        # Get the optional parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id')) \
            if 'application_id' in request.form \
            else -1

        # Get the application sessions.
        application_sessions: list[ApplicationSession] = database.get_user_application_sessions(user_id, application_id)

        return {'application_sessions': Utils.serialize(application_sessions, True)}, 200


class GetApplicationSessions(APIResource):
    required_parameters = ['application_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        application_id: int = Utils.safe_int_cast(request.form.get('application_id'))

        # Ensure that the application exists.
        application = database.get_application(application_id)

        if not application:
            return {'details': 'The specified application does not exist.'}, 400

        # Ensure that the user has the authority to access the application sessions.
        if not ((user in application.owners) or user.administrator):
            return {'details': 'You do not have the authority to access this application\'s session(s).'}, 403

        return {'application_sessions': Utils.serialize(application, user.administrator)}, 200


class CreatePhoto(APIResource):
    required_parameters = ['subfolder']
    required_files = ['photo']

    def post(self):
        missing_files, missing_files_list = self.missing_files()

        if missing_files:
            return {'details': 'You must provide a photo.'}, 400

        # Get the file.
        file = request.files['photo']

        # Get the parameters.
        subfolder = request.form.get('subfolder')

        # Save the file.
        filename = Utils.generate_uuid4() + secure_filename(file.filename)
        filepath = file_manager.generate_photo_filepath(subfolder, filename)

        file.save(filepath)

        # Create the photo's database record.
        database.create_photo(
            filename,
            subfolder,
            date.today()
        )

        return {}, 201


class GetPhoto(APIResource):
    required_parameters = ['id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        success, response, response_code, session, user = self.verify_session(database)

        if not success:
            return response, response_code

        # Get the parameters.
        id_: int = Utils.safe_int_cast(request.form.get('id'))

        # Ensure that the photo exists.
        photo = database.get_photo_by_id(id_)

        if not photo:
            return {'details': 'The specified photo does not exist.'}, 400

        return send_file(file_manager.get_photo_filepath(id_), 'image/png')


# Main method.
def main():
    global email_manager, database, database_utils, file_manager, app, api

    # Initialize the logger.
    logger.remove()
    logger.add('logs/frogworks_{time}.log', rotation='1 week', retention=5, level='INFO')
    logger.add(sys.stdout, level='INFO')

    # Load the .env environment variables.
    logger.info('Loading .env file.')
    load_dotenv()

    # Initialize the email manager.
    logger.info('Initializing email manager.')
    email_manager = EmailManager(os.getenv('EMAIL_ADDRESS'), os.getenv('APP_PASSWORD'), os.getenv('DISPLAY_NAME'))

    # Initialize the database.
    logger.info('Initializing database.')
    database = Database(email_manager)
    database.initialize()

    # Initialize the database utils.
    logger.info('Initializing database utils.')
    database_utils = DatabaseUtils(database)

    # Initialize the file manager.
    logger.info('Initializing file manager.')
    file_manager = FileManager(database, BASE_DIRECTORY, PHOTOS_DIRECTORY, APPLICATIONS_DIRECTORY)
    file_manager.initialize()

    # Load the HTTP server port.
    server_port: int = int(os.getenv('SERVER_PORT'))

    # Initialize the HTTP server.
    logger.info('Initializing Flask server.')
    app = Flask(__name__)
    api = Api(app)

    # Add the routes.
    logger.info('Adding API routes.')
    api.add_resource(Ping, '/api/ping')
    api.add_resource(RequestEmailVerification, '/api/email-verification/request')
    api.add_resource(CheckEmailVerification, '/api/email-verification/check')
    api.add_resource(Register, '/api/user/register')
    api.add_resource(Login, '/api/user/login')
    api.add_resource(GetUser, '/api/user/get')
    api.add_resource(AuthenticateSession, '/api/session/authenticate')
    api.add_resource(DeleteSession, '/api/session/delete')
    api.add_resource(DeleteSpecificSession, '/api/session/delete-specific')
    api.add_resource(CreateApplication, '/api/application/create')
    api.add_resource(GetApplication, '/api/application/get')
    api.add_resource(GetApplicationVersions, '/api/application/versions')
    api.add_resource(DownloadApplicationVersion, '/api/application/versions/download')
    api.add_resource(UpdateApplicationVersion, '/api/application/update-version')
    api.add_resource(CreateVersion, '/api/version/create')
    api.add_resource(CreateSale, '/api/sales/create')
    api.add_resource(GetActiveSale, '/api/sales/get')
    api.add_resource(GetAllActiveSales, '/api/sales/get-all')
    api.add_resource(DeleteSale, '/api/sales/delete')
    api.add_resource(GetTransactions, '/api/user/get-transactions')
    api.add_resource(GetTransaction, '/api/user/get-transaction')
    api.add_resource(GetPurchase, '/api/user/get-purchase')
    api.add_resource(GetDeposit, '/api/user/get-deposit')
    api.add_resource(GetApplicationKey, '/api/user/get-application-key')
    api.add_resource(GetApplicationKeys, '/api/user/get-application-keys')
    api.add_resource(PurchaseApplication, '/api/purchase/application')
    api.add_resource(PurchaseIAP, '/api/purchase/iap')
    api.add_resource(GetIAPRecords, '/api/user/get-iap-records')
    api.add_resource(GetSession, '/api/session/get')
    api.add_resource(SendFriendRequest, '/api/friend/send-request')
    api.add_resource(DeleteFriendRequest, '/api/friend/delete-request')
    api.add_resource(AcceptFriendRequest, '/api/friend/accept-request')
    api.add_resource(RemoveFriend, '/api/friend/remove')
    api.add_resource(SendInvite, '/api/user/send-invite')
    api.add_resource(GetInvites, '/api/user/get-invites')
    api.add_resource(GetInvite, '/api/user/get-invite')
    api.add_resource(DeleteInvite, '/api/user/delete-invite')
    api.add_resource(CreatePhoto, '/api/photo/create')
    api.add_resource(GetPhoto, '/api/photo/get')

    # Run the HTTP server.
    logger.info('Starting HTTP server.')
    app.run(
        host='0.0.0.0',
        port=server_port,
        debug=True
    )


if __name__ == '__main__':
    main()