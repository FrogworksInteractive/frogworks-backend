from datetime import datetime
from datetime import date


class ApplicationSession:
    def __init__(self, id_: int, user_id: int, application_id: int, date_: str, length: int):
        self.id: int = id_
        self.user_id: int = user_id
        self.application_id: int = application_id
        self.date: date = datetime.strptime(date_, '%Y-%m-%d')
        self.length: int = length