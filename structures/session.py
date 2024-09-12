from datetime import datetime
from datetime import date

from structures.structure import Structure


class Session(Structure):
    attributes = ['id', 'identifier', 'user_id', 'hostname', 'mac_address', 'platform', 'start_date', 'last_activity']

    def __init__(self, id_: int, identifier: str, user_id: int, hostname: str, mac_address: str, platform: str,
                 start_date: str, last_activity: str):
        self.id: int = id_
        self.identifier: str = identifier
        self.user_id: int = user_id
        self.hostname: str = hostname
        self.mac_address: str = mac_address
        self.platform: str = platform
        self.start_date: date = datetime.strptime(start_date, '%Y-%m-%d')
        self.last_activity: date = datetime.strptime(last_activity, '%Y-%m-%d')