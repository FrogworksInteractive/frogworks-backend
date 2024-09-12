from datetime import datetime
from datetime import date


class Purchase:
    def __init__(self, id_: int, application_id: int, iap_id: int, user_id: int, type_: str, source: str, price: str,
                 key: str, date_: str):
        from utils import Utils

        self.id: int = id_
        self.application_id: int = application_id
        self.iap_id: int = iap_id
        self.user_id: int = user_id
        self.type: str = type_
        self.source: str = source
        self.price: float = Utils.safe_float_cast(price)
        self.key: str = key
        self.date: date = datetime.strptime(date_, '%Y-%m-%d')