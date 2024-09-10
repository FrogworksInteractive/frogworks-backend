import json
from datetime import datetime
from datetime import date


class Invite:
    def __init__(self, id_: int, user_id: int, from_user_id: int, application_id: int, details: str, date_: str):
        self.id: int = id_
        self.user_id: int = user_id
        self.from_user_id: int = from_user_id
        self.application_id: int = application_id
        self.details: dict = json.loads(details)
        self.date: date = datetime.strptime(date_, "%Y-%m-%d")