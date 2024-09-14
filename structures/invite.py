import json
from datetime import datetime
from datetime import date

from structures.structure import Structure


class Invite(Structure):
    attributes = ['id', 'user_id', 'from_user_id', 'application_id', 'details', 'date']

    def __init__(self, id_: int, user_id: int, from_user_id: int, application_id: int, details: str, date_: str):
        self.id: int = id_
        self.user_id: int = user_id
        self.from_user_id: int = from_user_id
        self.application_id: int = application_id
        self.details: dict = json.loads(details)
        self.date: date = datetime.strptime(date_, "%Y-%m-%d").date()