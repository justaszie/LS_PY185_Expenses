import psycopg2
from psycopg2.extras import DictCursor
from textwrap import dedent
from functools import wraps

# Wrapping database queries with connection and cursor as context managers
def db_query(cursor_type=None):
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

    @db_query(DictCursor)
    def all_user_expenses(self, cursor, user_id):
        query = (
            """
            SELECT *
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            JOIN users u ON u.id = %s
            """
        )
        cursor.execute(query, (user_id, ))

        results = cursor.fetchall()

        return results

    @db_query()
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


    def close_connection(self):
        self.connection.close()
