class ApplicationKey:
    def __init__(self, id_: int, application_id: int, key: str, type_: str, redeemed: bool):
        self.id: int = id_
        self.application_id: int = application_id
        self.key: str = key
        self.type: str = type_
        self.redeemed: bool = redeemed