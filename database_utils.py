from database import Database


class DatabaseUtils:
    def __init__(self, database: Database):
        self.database: Database = database

    def user_owns(self, user_id: int, application_id: int) -> bool:
        # Verify that the specified user owns a copy of the specified application.
        return self.database.get_application_key_for(user_id, application_id) is not None
