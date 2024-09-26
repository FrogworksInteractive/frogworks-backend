from datetime import datetime
from datetime import date

from .activity import Activity
from .structure import Structure


class User(Structure):
    attributes = ['id', 'identifier', 'username', 'name', 'email_address', 'password', 'joined', 'balance',
                  'profile_photo_id', 'activity', 'developer', 'administrator', 'verified']
    private_attributes = ['email_address', 'password']

    def __init__(self, id_: int, identifier: str, username: str, name: str, email_address: str, password: str,
                 joined: str, balance: str, profile_photo_id: int, activity: str, developer: bool, administrator: bool,
                 verified: bool):
        from utils import Utils

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
        self.developer: bool = Utils.safe_bool_cast(developer)
        self.administrator: bool = Utils.safe_bool_cast(administrator)
        self.verified: bool = Utils.safe_bool_cast(verified)

    def has_developer_permissions(self) -> bool:
        return self.developer or self.administrator

    def is_or_admin(self, id_: int) -> bool:
        return (self.id == id_) or self.administrator
