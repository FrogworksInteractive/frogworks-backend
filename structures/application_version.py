from datetime import datetime
from datetime import date

from structures.structure import Structure


class ApplicationVersion(Structure):
    attributes = ['id', 'application_id', 'name', 'platform', 'release_date', 'filename', 'executable']

    def __init__(self, id_: int, application_id: int, name: str, platform: str, release_date: str, filename: str,
                 executable: str):
        self.id: int = id_
        self.application_id: int = application_id
        self.name: str = name
        self.platform: str = platform
        self.release_date: date = datetime.strptime(release_date, '%Y-%m-%d').date()
        self.filename: str = filename
        self.executable: str = executable