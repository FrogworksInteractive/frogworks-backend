from datetime import datetime
from datetime import date

from activity import Activity


class User:
    def __init__(self, id_: int, identifier: str, username: str, name: str, email_address: str, password: str,
                 joined: str, balance: str, profile_photo_id: int, activity: str):
        self.id: int = id_
        self.identifier: str = identifier
        self.username: str = username
        self.name: str = name
        self.email_address: str = email_address
        self.password: str = password
        self.joined: date = datetime.strptime(joined, '%Y-%m-%d').date()
        self.balance: float = float(balance)
        self.profile_photo_id: int = profile_photo_id
        self.activity: Activity = Activity(activity)
