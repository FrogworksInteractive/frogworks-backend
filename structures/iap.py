import json


class IAP:
    def __init__(self, id_: int, application_id: int, title: str, description: str, price: str, data: str):
        self.id: int = id_
        self.application_id: int = application_id
        self.title: str = title
        self.description: str = description
        self.price: float = float(price)
        self.data: dict = json.loads(data)