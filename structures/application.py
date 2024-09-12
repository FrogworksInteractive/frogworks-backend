from datetime import datetime
from datetime import date


class Application:
    def __init__(self, id_: int, name: str, package_name: str, type_: str, description: str, release_date: str, early_access: bool,
                 latest_version: str, supported_platforms: str, genres: str, tags: str, base_price: str, owners: str):
        self.id: int = id_
        self.name: str = name
        self.package_name: str = package_name
        self.type: str = type_
        self.description: str = description
        self.release_date: date = datetime.strptime(release_date, '%Y-%m-%d').date()
        self.early_access: bool = early_access
        self.latest_version: str = latest_version
        self.supported_platforms: list = supported_platforms.split(',')
        self.genres: list = genres.split(',')
        self.tags: list = tags.split(',')
        self.base_price: float = float(base_price)
        self.owners: list = [int(owner) for owner in owners.split(',')]