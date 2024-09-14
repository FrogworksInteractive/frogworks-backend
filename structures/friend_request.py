from datetime import datetime
from datetime import date

from structures.structure import Structure


class FriendRequest(Structure):
    attributes = ['id', 'user_id', 'from_user_id', 'date']

    def __init__(self, id_: int, user_id: int, from_user_id: int, date_: str):
        self.id: int = id_
        self.user_id: int = user_id
        self.from_user_id: int = from_user_id
        self.date: date = datetime.strptime(date_, '%Y-%m-%d').date()