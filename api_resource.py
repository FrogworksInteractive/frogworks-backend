from flask import request
from flask_restful import Resource

from database import Database
from structures.session import Session
from structures.user import User


class APIResource(Resource):
    required_parameters: list = []
    required_files: list = []

    def missing_parameters(self) -> tuple[bool, list]:
        parameters = [parameter for parameter in self.required_parameters if parameter not in request.form]

        return len(parameters) > 0, parameters

    def missing_files(self) -> tuple[bool, list]:
        files = [file for file in self.required_files if file not in request.files]

        return len(files) > 0, files

    def verify_session(self, database: Database) -> tuple[bool, dict, int, Session | None, User | None]:
        missing, parameters = self.missing_parameters()

        if missing:
            return False, {'missing_parameters': parameters}, 400, None, None

        # Ensure that the user is authenticated.
        authenticated, session_id = self.get_authentication()

        if not authenticated:
            return False, {}, 401, None, None

        session = database.get_session(session_id)

        if not session:
            return False, {}, 403, None, None

        # Get the user.
        user = database.get_user(session.user_id)

        # Ensure that the user exists.
        if not user:
            return False, {'details': 'The session\'s user does not exist.'}, 400, None, None

        return True, {}, -1, session, user

    @staticmethod
    def get_authentication() -> tuple[bool, str | None]:
        auth_header = request.headers.get('SessionId')

        if auth_header:
            return True, auth_header
        else:
            return False, None
