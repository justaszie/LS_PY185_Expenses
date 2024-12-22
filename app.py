from flask import (
    Flask,
    render_template,
)
from secrets import token_hex

app = Flask(__name__)
app.secret_key = token_hex(32)

@app.route('/')
def index():
    return render_template('expense_list.html')

if __name__ == '__main__':
    app.run(debug=True, port=5020)
