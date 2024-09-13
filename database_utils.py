from database import Database


class DatabaseUtils:
    def __init__(self, database: Database):
        self.database: Database = database

    def user_owns_key_for(self, user_id: int, application_id: int) -> bool:
        # Verify that the specified user owns a copy of the specified application.
        return self.database.get_application_key_for(user_id, application_id) is not None

    def user_owns(self, user_id: int, application_id: int) -> bool:
        # Check if they own a key for the application.
        owns_key = self.user_owns_key_for(user_id, application_id)

        if owns_key:
            return True

        # Check if they are an administrator, or own the game itself.
        # Get the user.
        user = self.database.get_user(user_id)

        # Get the application.
        application = self.database.get_application(application_id)

        return user.administrator or user.id in application.owners
