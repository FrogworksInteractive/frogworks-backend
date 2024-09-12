from datetime import datetime
from datetime import date


class ApplicationVersion:
    def __init__(self, id_: int, application_id: int, name: str, platform: str, release_date: str, filename: str):
        self.id: int = id_
        self.application_id: int = application_id
        self.name: str = name
        self.platform: str = platform
        self.release_date: date = datetime.strptime(release_date, '%Y-%m-%d').date()
        self.filename: str = filename