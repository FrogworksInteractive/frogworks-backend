import os

from dotenv import load_dotenv
from datetime import datetime
from datetime import date

# Flask-related imports.
from flask import Flask, request
from flask_restful import Api

# Local imports.
from database import Database
from email_manager import EmailManager
from api_resource import APIResource
from file_manager import FileManager
from structures.user import User
from utils import Utils


# Constants.
BASE_DIRECTORY: str = 'data'
PHOTOS_DIRECTORY: str = 'photos'
APPLICATIONS_DIRECTORY: str = 'applications'


# Variables.
email_manager: EmailManager | None = None
database: Database | None = None
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
        version_file.save(file_manager.generate_version_filepath(application.package_name, filename))

        return response, 200


class GetVersions(APIResource):
    required_parameters = ['application_id']

    def get(self):
        missing, parameters = self.missing_parameters()

        if missing:
            return {'missing_parameters': parameters}, 400

        authenticated, session_id = self.get_authentication()

        if not authenticated:
            return {}, 401


# Main method.
def main():
    global email_manager, database, file_manager, app, api

    # Load the .env environment variables.
    load_dotenv()

    # Initialize the email manager.
    email_manager = EmailManager(os.getenv('EMAIL_ADDRESS'), os.getenv('APP_PASSWORD'), os.getenv('DISPLAY_NAME'))

    # Initialize the database.
    database = Database(email_manager)
    database.initialize()

    # Initialize the file manager.
    file_manager = FileManager(database, BASE_DIRECTORY, PHOTOS_DIRECTORY, APPLICATIONS_DIRECTORY)
    file_manager.initialize()

    # Load the HTTP server port.
    server_port: int = int(os.getenv('SERVER_PORT'))

    # Initialize the HTTP server.
    app = Flask(__name__)
    api = Api(app)

    # Add the routes.
    api.add_resource(Ping, '/api/ping')
    api.add_resource(RequestEmailVerification, '/api/email-verification/request')
    api.add_resource(CheckEmailVerification, '/api/email-verification/check')
    api.add_resource(Register, '/api/user/register')
    api.add_resource(Login, '/api/user/login')
    api.add_resource(GetUser, '/api/user/get')
    api.add_resource(AuthenticateSession, '/api/session/authenticate')
    api.add_resource(DeleteSession, '/api/session/delete')
    api.add_resource(CreateApplication, '/api/application/create')
    api.add_resource(GetApplication, '/api/application/get')
    api.add_resource(UpdateApplicationVersion, '/api/application/update-version')
    api.add_resource(CreateVersion, '/api/version/create')

    # Run the HTTP server.
    app.run(
        host='0.0.0.0',
        port=server_port,
        debug=True
    )


if __name__ == '__main__':
    main()