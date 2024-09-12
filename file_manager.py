import os
from os import path

from database import Database
from structures.application_version import ApplicationVersion
from structures.photo import Photo


class FileManager:
    def __init__(self, database: Database, base_directory: str, photos_directory: str, applications_directory: str):
        # Calculate all the paths.
        self.database: Database = database
        self.base_directory = path.join(os.getcwd(), base_directory)
        self.photos_directory: str = path.join(self.base_directory, photos_directory)
        self.applications_directory: str = path.join(self.base_directory, applications_directory)

    def initialize(self):
        # Ensure that all the required data directories exist.
        os.makedirs(self.base_directory, exist_ok=True)
        os.makedirs(self.photos_directory, exist_ok=True)
        os.makedirs(self.applications_directory, exist_ok=True)

    def get_photo_filepath(self, image_id) -> str | None:
        # Get the image's database entry.
        image: Photo | None = self.database.get_photo_by_id(image_id)

        if image is None:
            return None

        return path.join(self.photos_directory, image.subfolder, image.filename)

    def get_version_filepath(self, version_id) -> str | None:
        # Get the version.
        version: ApplicationVersion | None = self.database.get_application_version_by_id(version_id)

        if version is None:
            return None

        # Get the application.
        application = self.database.get_application(version.application_id)

        if application is None:
            return None

        return path.join(self.applications_directory, application.package_name, version.filename)

    def create_application_folder(self, package_name: str):
        os.makedirs(path.join(self.applications_directory, package_name), exist_ok=True)

    def generate_photo_filepath(self, subfolder: str, filename: str) -> str:
        return path.join(self.photos_directory, subfolder, filename)

    def generate_version_filepath(self, package_name: str, filename: str) -> str:
        return path.join(self.applications_directory, package_name, filename)
