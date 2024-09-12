import os

from dotenv import load_dotenv
from datetime import date

# Flask-related imports.
from flask import Flask, request
from flask_restful import Api

# Local imports.
from database import Database
from email_manager import EmailManager
from api_resource import APIResource
from structures.user import User
from utils import Utils

# Variables.
email_manager: EmailManager | None = None
database: Database | None = None
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
            return {'missing_parameters': missing}, 400

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
            return {'missing_parameters': missing}, 400

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
            return {'missing_parameters': missing}, 400

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
            return {'missing_parameters': missing}, 400

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


# Main method.
def main():
    global email_manager, database, app, api

    # Load the .env environment variables.
    load_dotenv()

    # Initialize the email manager.
    email_manager = EmailManager(os.getenv('EMAIL_ADDRESS'), os.getenv('APP_PASSWORD'), os.getenv('DISPLAY_NAME'))

    # Initialize the database.
    database = Database(email_manager)
    database.initialize()

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
    api.add_resource(AuthenticateSession, '/api/session/authenticate')

    # Run the HTTP server.
    app.run(
        host='0.0.0.0',
        port=server_port,
        debug=True
    )


if __name__ == '__main__':
    main()