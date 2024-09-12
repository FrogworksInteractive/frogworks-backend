from flask import request
from flask_restful import Resource


class APIResource(Resource):
    required_parameters: list = []

    def missing_parameters(self) -> tuple[bool, list]:
        parameters = [parameter for parameter in self.required_parameters if parameter not in request.form]

        return len(parameters) > 0, parameters

    @staticmethod
    def get_authentication() -> tuple[bool, str | None]:
        auth_header = request.headers.get('SessionId')

        if auth_header:
            return True, auth_header
        else:
            return False, None