import os

from dotenv import load_dotenv

# Flask-related imports.
from flask import Flask, request
from flask_restful import Resource, Api

# Local imports.
from database import Database
from email_manager import EmailManager
from api_resource import APIResource
from utils import Utils

# Variables.
email_manager: EmailManager | None = None
database: Database | None = None
app = None
api = None


# Api classes.
class Ping(APIResource):
    def get(self):
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

    # Run the HTTP server.
    app.run(
        host='0.0.0.0',
        port=server_port,
        debug=True
    )


if __name__ == '__main__':
    main()