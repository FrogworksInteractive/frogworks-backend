import os

from dotenv import load_dotenv

from database import Database
from email_manager import EmailManager


database = None


def main():
    global database

    # Load the .env environment variables.
    load_dotenv()

    # Initialize the email manager`
    email_manager = EmailManager(os.getenv('EMAIL_ADDRESS'), os.getenv('APP_PASSWORD'), os.getenv('DISPLAY_NAME'))

    # Initialize the database.
    database = Database(email_manager)
    database.initialize()


if __name__ == '__main__':
    main()