from datetime import datetime
from datetime import date

from structures.structure import Structure


class Transaction(Structure):
    attributes = ['id', 'user_id', 'transaction_id', 'type', 'date']

    def __init__(self, id_: int, user_id: int, transaction_id: int, type_: str, date_: str):
        self.id: int = id_
        self.user_id: int = user_id
        self.transaction_id: int = transaction_id
        self.type: str = type_
        self.date: date = datetime.strptime(date_, '%Y-%m-%d').date()