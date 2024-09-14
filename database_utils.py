from datetime import date

from database import Database
from utils import Utils


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

    def get_application_price(self, application_id: int) -> float:
        # Get the current price for a specific application.
        # Get the base price.
        application = self.database.get_application(application_id)
        base_price: float = application.base_price

        # Check if there is a sale going on currently.
        sale = self.database.get_active_sale(application_id, date.today())

        if sale is None:
            return base_price

        return sale.price

    def get_iap_price(self, iap_id: int) -> float:
        return self.database.get_iap(iap_id).price

    def purchase(self, user_id: int, application_id: int, for_user_id: int, iap_id: int = -1) -> tuple[bool, dict]:
        # Purchase something (application or in-app purchase [iap])
        # Ensure that the application exists.
        application = self.database.get_application(application_id)

        if application is None:
            return False, {'details': 'The specified application does not exist.'}

        # Decide what type the purchase is.
        type_: str = 'application' if iap_id == -1 else 'iap'

        # Get the price.
        price: float = self.get_application_price(application_id) if iap_id == -1 else self.get_iap_price(iap_id)

        # Get the users.
        user = self.database.get_user(user_id)
        for_user = user if for_user_id == user_id else self.database.get_user(for_user_id)

        # Check the balance of the user who is paying.
        if user.balance < price:
            return False, {'details': 'The user\'s balance is less than the price.'}

        # The user's balance is enough; proceed to purchase.
        success, response = (
            self.__purchase_application(for_user_id, application_id)) if iap_id == -1 \
            else self.__purchase_iap(application_id, iap_id)

        if not success:
            return False, response

        # Figure out the source type.
        source: str = 'self' if for_user_id == user_id else 'gift'

        # Get the application key (if applicable).
        application_key: str = '' if type_ == 'iap' else response['application_key']

        # Get today's date.
        today: date = date.today()

        # Create the purchase record.
        transaction_id: int = self.database.create_purchase(
            application_id,
            iap_id,
            for_user_id,
            type_,
            source,
            str(price),
            application_key,
            today
        )

        # Create the transaction record.
        self.database.create_transaction(
            user_id,
            transaction_id,
            'purchase',
            today
        )

        # Update the user's balance.
        self.database.update_user_property(user_id, 'balance', user.balance - price)

        return True, {'details': 'Purchase succeeded.', 'transaction_id': transaction_id}

    def __purchase_application(self, user_id: int, application_id: int) -> tuple[bool, dict]:
        # Purchase an application.
        # Ensure that the application exists.
        application = self.database.get_application(application_id)

        if application is None:
            return False, {'details': 'The specified application does not exist.'}

        # Ensure that the user exists.
        user = self.database.get_user(user_id)

        if user is None:
            return False, {'details': 'The specified user does not exist.'}

        # Ensure that the specified user does not already own the application.
        if self.user_owns_key_for(user_id, application_id):
            return False, {'details': 'The user already owns the specified application.'}

        # Ensure that the user's balance is enough to purchase the application.
        application_price: float = self.get_application_price(application_id)

        if application_price > user.balance:
            return False, {'details': 'The user\'s balance is less than the price of the application.'}

        # The user's balance is enough to purchase the application; continue.
        # Create an application key.
        application_key: str = Utils.generate_product_key()
        success, response = self.database.create_application_key(
            application_id,
            application_key,
            'purchase',
            True,
            user_id
        )

        if not success:
            return False, response

        return True, {'details': 'The purchased application was successful.', 'application_key': application_key}

    def __purchase_iap(self, user_id: int, iap_id: int) -> tuple[bool, dict]:
        # Ensure that the iap actually exists.
        iap = self.database.get_iap(iap_id)

        if iap is None:
            return False, {'details': 'The specified iap does not exist.'}

        # The iap exists. Now ensure that the user exists.
        user = self.database.get_user(user_id)

        if user is None:
            return False, {'details': 'The specified user does not exist.'}

        # Create the iap record.
        self.database.create_iap_record(
            iap_id,
            user_id,
            date.today()
        )

        return True, {'details': 'The iap purchase was successful.'}

    def get_purchase_source(self, purchase_id: int) -> int | None:
        # Ensure that the purchase exists.
        purchase = self.database.get_purchase(purchase_id)

        if purchase is None:
            return None

        # Get the related transaction through reverse lookup.
        transaction = self.database.get_transaction_for(purchase_id)

        if transaction is None:
            return None

        return transaction.user_id
