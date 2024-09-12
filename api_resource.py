from flask import request
from flask_restful import Resource


class APIResource(Resource):
    required_parameters: list = []
    required_files: list = []

    def missing_parameters(self) -> tuple[bool, list]:
        parameters = [parameter for parameter in self.required_parameters if parameter not in request.form]

        return len(parameters) > 0, parameters

    def missing_files(self) -> tuple[bool, list]:
        files = [file for file in self.required_files if file not in request.files]

        return len(files) > 0, files

    @staticmethod
    def get_authentication() -> tuple[bool, str | None]:
        auth_header = request.headers.get('SessionId')

        if auth_header:
            return True, auth_header
        else:
            return False, None