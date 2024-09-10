from datetime import datetime
from datetime import date


class Deposit:
    def __init__(self, id_: int, user_id: int, amount: str, source: str, date_: str):
        self.id: int = id_
        self.user_id = user_id
        self.amount: float = float(amount)
        self.source: str = source
        self.date: date = datetime.strptime(date_, '%Y-%m-%d')