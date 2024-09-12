from datetime import datetime
from datetime import date


class Sale:
    def __init__(self, id_: int, application_id: int, title: str, description: str, price: str, start_date: str,
               end_date: str):
        from utils import Utils

        self.id: int = id_
        self.application_id: int = application_id
        self.title: str = title
        self.description: str = description
        self.price: float = Utils.safe_float_cast(price)
        self.start_date: date = datetime.strptime(start_date, '%Y-%m-%d').date()
        self.end_date: date = datetime.strptime(end_date, '%Y-%m-%d').date()