from datetime import datetime
from datetime import date

from structures.structure import Structure


class Deposit(Structure):
    attributes = ['id', 'user_id', 'amount', 'source', 'date']

    def __init__(self, id_: int, user_id: int, amount: str, source: str, date_: str):
        from utils import Utils

        self.id: int = id_
        self.user_id = user_id
        self.amount: float = Utils.safe_float_cast(amount)
        self.source: str = source
        self.date: date = datetime.strptime(date_, '%Y-%m-%d')