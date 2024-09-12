from structures.structure import Structure


class ApplicationKey(Structure):
    attributes = ['id', 'application_id', 'key', 'type', 'redeemed', 'user_id']

    def __init__(self, id_: int, application_id: int, key: str, type_: str, redeemed: bool, user_id: int):
        from utils import Utils

        self.id: int = id_
        self.application_id: int = application_id
        self.key: str = key
        self.type: str = type_
        self.redeemed: bool = Utils.safe_bool_cast(redeemed)
        self.user_id: int = user_id