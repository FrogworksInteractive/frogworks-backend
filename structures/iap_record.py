from datetime import datetime
from datetime import date

from structures.structure import Structure


class IAPRecord(Structure):
    attributes = ['id', 'iap_id', 'user_id', 'application_id', 'date', 'acknowledged']

    def __init__(self, id_: int, iap_id: int, user_id: int, application_id: int, date_: str, acknowledged: bool):
        from utils import Utils

        self.id: int = id_
        self.iap_id: int = iap_id
        self.user_id: int = user_id
        self.application_id: int = application_id
        self.date: date = datetime.strptime(date_, '%Y-%m-%d').date()
        self.acknowledged: bool = Utils.safe_bool_cast(acknowledged)
