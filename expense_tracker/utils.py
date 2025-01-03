
from datetime import datetime
from expense_tracker.db_storage import ExpensesDatabaseStorage
from flask import g
import re
import bcrypt

def extract_expense_data(form_data):
    # Define a list of attribute names
    attributes = (
        'transaction_date',
        'transaction_time',
        'amount_usd',
        'description',
        'category_id',
    )
    expense_data = {
        attr_name: form_data.get(attr_name, '').strip()
        for attr_name in attributes
    }
    return expense_data


def errors_for_transaction_datetime(transaction_date, transaction_time):
    """
    Rules:
    1. Attributes come in string format.
    2. date is mandatory. Must be able to create a date object. If not, incorrect format
    3. time is not mandatory. If present, must be able to create a time value by parsing. If not, incorrect format.
    """
    if not transaction_date:
        return ['Transaction Date is mandatory']

    if transaction_time:
        try:
            transaction_datetime = datetime.strptime(f'{transaction_date}T{transaction_time}','%Y-%m-%dT%H:%M')
        except ValueError:
            return ['Wrong format for Transaction Date or Time']
    else:
        try:
            transaction_datetime = datetime.strptime(f'{transaction_date}','%Y-%m-%d')
        except ValueError:
            return ['Wrong format for Transaction Date']

    if transaction_datetime > datetime.now():
        return ['Transaction Date / Time cannot be in the future']

    return []

def errors_for_transaction_amount(amount_str):
    if not amount_str:
        return ['Transaction Amount is mandatory']

    try:
        amount = float(amount_str)
    except ValueError:
        return ['Transaction Amount must be a number']

    if amount < 0:
        return ['Transaction Amount must be positive']

    return []

def errors_for_expense_description(description):
    if not description:
        return ['Transaction Description is mandatory']

    if not 2 < len(description) < 150:
        return [
            'Transaction Description must be between 2 '
            'and 150 characters'
        ]

    return []

def errors_for_expense_category(category_id_str):
    if category_id_str:
        try:
            category_id = int(category_id_str)
        except ValueError:
            return ['Category value is not supported. Make sure you selected a value from the list']

        categories = [cat['id'] for cat in g.storage.get_categories()]
        if category_id not in categories:
            return ['Category value is not supported. Make sure you selected a value from the list']

    return []

def expense_data_errors(expense_data):
    errors = []

    # Error checking for datetime is specific
    # because it's based on 2 form fields attributes
    datetime_errors = errors_for_transaction_datetime(
        expense_data['transaction_date'],
        expense_data['transaction_time']
    )

    errors.extend(datetime_errors)

    # Run through all the other error checker functions,
    # and collect errors from them
    error_checkers = {
        'amount_usd': errors_for_transaction_amount,
        'description': errors_for_expense_description,
        'category_id': errors_for_expense_category,
    }

    for attribute_name, error_checker in error_checkers.items():
        input_data = expense_data[attribute_name]
        errors.extend(error_checker(input_data))

    return errors

# def sort_by_transaction_date(expenses):
#     return sorted(expenses, key=lambda x: x.get('transaction_datetime'), reverse=True)

def errors_for_username(username):
    errors = []
    if not username:
        return ['Username is required.']

    if g.storage.username_exists(username):
        errors.append('Username already exists. Try a different one.')

    if not 3 <= len(username) <= 20:
        errors.append('Username must be between 3 and 20 characters')

    return errors

def errors_for_password(password):
    errors = []
    if not password:
        return ['Password is required.']

    pwd_pattern = r'([a-z]+.*[A-Z]+.*|[A-Z]+.*[a-z]+.*)'
    match = re.search(pwd_pattern, password)
    if not match:
        errors.append('Password must contain at least 1 uppercase letter and 1 lowercase letter')

    if len(password) < 5:
        errors.append('Password must be at least 5 characters')

    return errors

def sign_up_credentials_errors(username, password):
    errors = []
    errors.extend(errors_for_username(username))
    errors.extend(errors_for_password(password))

    return errors

def get_hashed_password(password):
    salt = bcrypt.gensalt()
    password_bytes = password.encode('utf-8')
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    return password_hash

def valid_credentials(username, password):
    user_id = g.storage.find_user_by_username(username)
    if not user_id:
        return False

    stored_credentials = g.storage.get_user_credentials(user_id)
    stored_password = stored_credentials['user_password'].encode('utf-8')
    entered_password = password.encode('utf-8')

    return bcrypt.checkpw(entered_password, stored_password)