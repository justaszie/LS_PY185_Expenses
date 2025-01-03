from datetime import datetime, date
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    g,
    session,
    abort,
    request,
    flash
)
from secrets import token_hex
from expense_tracker.db_storage import ExpensesDatabaseStorage
from functools import wraps
from expense_tracker import utils

app = Flask(__name__)
app.secret_key = token_hex(32)
# app.jinja_env.filters['sort_expenses'] = utils.sort_by_transaction_date

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
    if not hasattr(g, 'storage'):
        g.storage = ExpensesDatabaseStorage()

# TODO - Implement properly when working on auth
@app.before_request
def initialize_session():
    session['user_name'] = 'admin'

@app.teardown_appcontext
def teardown_db(exception=None):
    if hasattr(g, 'storage'):
        g.storage.close_connection()


@app.route('/')
def index():
    return redirect(url_for('expense_list'))

@app.route('/expenses')
@requires_signin
def expense_list(user_id):
    expenses = g.storage.get_all_user_expenses(user_id)

    for expense in expenses:
        expense['amount_usd'] = expense.pop('amount_cents_usd') / 100
        expense['transaction_datetime'] = expense['transaction_datetime'].strftime('%Y-%m-%d %H:%M')

    return render_template('expense_list.html', expenses=expenses)

@app.route('/expenses/new')
def new_expense_view():
    categories = g.storage.get_categories()
    return render_template('add_expense.html', categories=categories, current_date=date.today())

@app.route('/expenses', methods=['POST'])
@requires_signin
def create_expense(user_id):
    expense_data = utils.extract_expense_data(request.form)

    errors = utils.expense_data_errors(expense_data)
    if errors:
        for error in errors:
            flash(error, 'error')

        categories = g.storage.get_categories()
        return render_template('add_expense.html', categories=categories, current_date=date.today())

    try:
        expense_id = g.storage.create_new_expense(user_id, **expense_data)
        if expense_id:
            flash('Expense created successfully', 'success')
            return redirect(url_for('expense_list'))
        else:
            abort(500)
    except ValueError:
        abort(500)

@app.route('/expenses/<int:expense_id>/edit', methods=['GET'])
@requires_signin
def edit_expense_view(user_id, expense_id):
    categories = g.storage.get_categories()

    # TODO - move this to a decorator later
    expense = g.storage.find_expense_by_id(user_id, expense_id)
    if not expense:
        abort(404, description='Expense not found')

    expense['transaction_date'] = expense['transaction_datetime'].strftime('%Y-%m-%d')
    expense['transaction_time'] = expense['transaction_datetime'].strftime('%H:%M')
    expense['amount_usd'] = expense.pop('amount_cents_usd') / 100
    return render_template('edit_expense.html', expense=expense, categories=categories)

@app.route('/expenses/<int:expense_id>/edit', methods=['POST'])
@requires_signin
def edit_expense(user_id, expense_id):
    expense_data = utils.extract_expense_data(request.form)

    errors = utils.expense_data_errors(expense_data)
    if errors:
        for error in errors:
            flash(error, 'error')

        categories = g.storage.get_categories()
        expense_data['id'] = expense_id
        return render_template('edit_expense.html', expense=expense_data, categories=categories)

    else:
        try:
            g.storage.update_expense(user_id, expense_id, **expense_data)
            flash('Expense updated successfully', 'success')
            return redirect(url_for('expense_list'))
        except ValueError:
            abort(500)

@app.route('/expenses/<int:expense_id>/delete', methods=['POST'])
@requires_signin
def delete_expense(user_id, expense_id):
    g.storage.delete_expense_by_id(user_id, expense_id)
    flash('Expense deleted successfully', 'success')
    return redirect(url_for('expense_list'))

@app.route('/analytics', methods=['GET'])
@requires_signin
def analytics_view(user_id):
    if request.args:
        if request.args.get('grouping_option'):
            print(request.args)
            grouping_option = request.args.get('grouping_option')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')

            groups_data = g.storage.get_grouped_data(user_id, grouping_option, date_from, date_to)
            for group in groups_data:
                group['group_value'] = group['group_value'].strftime('%Y-%m-%d')
                group['total_amount'] = f'{(group['total_amount'] / 100):.2f}'
                group['avg_amount'] = f'{(group['avg_amount'] / 100):.2f}'

            return render_template('analytics.html', groups_data=groups_data)
        else:
            flash('You must select a grouping option', 'error')
            return render_template('analytics.html')


    return render_template('analytics.html')

if __name__ == '__main__':
    app.run(debug=True, port=5020)
