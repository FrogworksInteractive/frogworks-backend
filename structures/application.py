from datetime import datetime
from datetime import date

from structures.structure import Structure


class Application(Structure):
    attributes = ['id', 'name', 'package_name', 'type', 'description', 'release_date', 'early_access',
                         'latest_version', 'supported_platforms', 'genres', 'tags', 'base_price', 'owners']

    def __init__(self, id_: int, name: str, package_name: str, type_: str, description: str, release_date: str,
                 early_access: bool, latest_version: str, supported_platforms: str, genres: str, tags: str,
                 base_price: str, owners: str):
        from utils import Utils

        self.id: int = id_
        self.name: str = name
        self.package_name: str = package_name
        self.type: str = type_
        self.description: str = description
        self.release_date: date = datetime.strptime(release_date, '%Y-%m-%d').date()
        self.early_access: bool = Utils.safe_bool_cast(early_access)
        self.latest_version: str = latest_version
        self.supported_platforms: list = supported_platforms.split(',')
        self.genres: list = genres.split(',')
        self.tags: list = tags.split(',')
        self.base_price: float = Utils.safe_float_cast(base_price)
        self.owners: list = [int(owner) for owner in owners.split(',')]
