import psycopg2
from psycopg2.extras import DictCursor
from textwrap import dedent
from functools import wraps
from datetime import datetime

# Wrapping database queries with connection and cursor as context managers
def db_transaction(cursor_type=None):
    def decorator(meth):
        @wraps(meth)
        def wrapper(self, *args, **kwargs):
            with self.connection:
                if cursor_type:
                    with self.connection.cursor(cursor_factory=cursor_type) as cursor:
                        result = meth(self, cursor, *args, **kwargs)
                else:
                    with self.connection.cursor() as cursor:
                        result = meth(self, cursor, *args, **kwargs)
                return result
        return wrapper
    return decorator


class ExpensesDatabaseStorage:
    def __init__(self, is_test_env=False):
        db_name = 'test_expenses' if is_test_env else 'expenses'
        self.connection = psycopg2.connect(dbname=db_name)

    @db_transaction(DictCursor)
    def all_user_expenses(self, cursor, user_id):
        query = (
            """
            SELECT e.*, c.name as category_name
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            JOIN users u ON u.id = e.user_id
            WHERE u.id = %s
            """
        )
        cursor.execute(query, (user_id, ))

        rows = cursor.fetchall()
        results = [dict(row) for row in rows]

        return results

    @db_transaction(DictCursor)
    def find_expense_by_id(self, cursor, user_id, expense_id):
        query = (
            """
            SELECT e.*, c.name as category_name
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            JOIN users u ON u.id = e.user_id
            WHERE u.id = %s
                AND e.id = %s
            """
        )
        params = (user_id, expense_id,)

        cursor.execute(query, params)
        result = cursor.fetchone()
        return dict(result) if result else None

    @db_transaction()
    def get_current_user_id(self, cursor, user_name):
        query = (
            """
            SELECT id
            FROM users
            WHERE LOWER(user_name) = %s
            """
        )
        cursor.execute(query, (user_name.lower(), ))

        result = cursor.fetchone()
        return result[0] if result else None

    @db_transaction(DictCursor)
    def get_categories(self, cursor):
        query = (
            """
            SELECT *
            FROM categories
            ORDER BY name ASC
            """
        )
        cursor.execute(query)
        return cursor.fetchall()

    def close_connection(self):
        self.connection.close()

    @db_transaction()
    def create_new_expense(self, cursor, user_id,
                           transaction_date, transaction_time,
                           amount_usd, description, category_id):
        amount_cents = float(amount_usd) * 100
        if transaction_time:
            transaction_datetime = datetime.strptime(f'{transaction_date}T{transaction_time}','%Y-%m-%dT%H:%M')
        else:
            transaction_datetime = datetime.strptime(f'{transaction_date}','%Y-%m-%d')
        category_id = int(category_id) if category_id else None
        description = description if description else None

        query = (
            """
            INSERT INTO expenses
            (transaction_datetime, amount_cents_usd, description,
            user_id, category_id)
            VALUES
            (%s, %s, %s, %s, %s)
            RETURNING ID
            """
        )
        params = (transaction_datetime, amount_cents, description,
                  user_id, category_id, )

        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else None

    @db_transaction()
    def update_expense(self, cursor, user_id, expense_id, **expense_data):
        pass
