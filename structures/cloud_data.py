import json
from datetime import date
from datetime import datetime

from structures.structure import Structure


class CloudData(Structure):
    attributes = ['id', 'user_id', 'application_id', 'data', 'date']

    def __init__(self, id_: int, user_id: int, application_id: int, data: str, date_: str):
        self.id: int = id_
        self.user_id: int = user_id
        self.application_id: int = application_id
        self.data: dict = json.loads(data)
        self.date: date = datetime.strptime(date_, '%Y-%m-%d').date()