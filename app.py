from datetime import datetime
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    g,
    session,
    abort
)
from secrets import token_hex
from expense_tracker.db_storage import ExpensesDatabaseStorage
from functools import wraps

app = Flask(__name__)
app.secret_key = token_hex(32)

def requires_signin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_name = session.get('user_name')
        if not user_name:
            abort(401, description='You must be signed in')

        user_id = g.storage.get_current_user_id(user_name)
        return func(user_id, *args, **kwargs)
    return wrapper


@app.before_request
def create_db_connection():
    g.storage = ExpensesDatabaseStorage()

# TODO - Implement properly when working on auth
@app.before_request
def initialize_session():
    session['user_name'] = 'admin'

@app.teardown_appcontext
def close_db_connection(exception=None):
    if hasattr(g, 'storage'):
        g.storage.close_connection()


@app.route('/')
def index():
    return redirect(url_for('expense_list'))

@app.route('/expenses')
@requires_signin
def expense_list(user_id):
    expenses = g.storage.all_user_expenses(user_id)
    # expenses=[
    #     {
    #         'id': 12,
    #         'expense_date_time': datetime.now(),
    #         'amount_usd': 121.20,
    #         'description': 'Berneliu Uzeiga',
    #         'category': 'food'
    #     },
    # ]
    return render_template('expense_list.html', expenses=expenses)

if __name__ == '__main__':
    app.run(debug=True, port=5020)
