from datetime import datetime
from datetime import date

from structures.structure import Structure


class Photo(Structure):
    attributes = ['id', 'filename', 'subfolder', 'created_at']

    def __init__(self, id_: int, filename: str, subfolder: str, created_at: str):
        self.id: int = id_
        self.filename: str = filename
        self.subfolder: str = subfolder
        self.created_at: date = datetime.strptime(created_at, '%Y-%m-%d').date()