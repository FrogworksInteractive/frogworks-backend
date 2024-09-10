from datetime import datetime
from datetime import date


class Photo:
    def __init__(self, id_: int, filename: str, subfolder: str, created_at: str):
        self.id: int = id_
        self.filename: str = filename
        self.subfolder: str = subfolder
        self.created_at: date = datetime.strptime(created_at, '%Y-%m-%d')