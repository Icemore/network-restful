from datetime import datetime
import os

from flask import Flask, abort, render_template, g
from requests.exceptions import HTTPError

from currency_view import CurrencyResponse
from task_view import TaskView
from currency import *
from content_parsing import respond
from db import close_db


app = Flask(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'currency.db'),
    DEBUG=False,
    HOST="0.0.0.0",
    PORT=80
))
app.teardown_appcontext_funcs.append(close_db)

@app.before_request
def init():
    g.app = app

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/currency/<path:date>')
def currency(date):
    try:
        date = datetime.strptime(date, date_format)
        price = get_currency_price(date)

        if price is None:
            abort(404)

        return respond(CurrencyResponse(price, date))
    except ValueError:
        abort(400)
    except HTTPError:
        abort(502)


task_view = TaskView.as_view('tasks')
app.add_url_rule('/tasks', defaults={'task_id': None},
                 view_func=task_view, methods=['GET'], endpoint='tasks')
app.add_url_rule('/tasks', view_func=task_view, methods=['PUT'], endpoint='add_task')
app.add_url_rule('/tasks/<int:task_id>', view_func=task_view,
                 methods=['GET', 'POST', 'DELETE'], endpoint='task')

if __name__ == '__main__':
    app.run(host=app.config['HOST'], debug=app.config['DEBUG'], port=app.config['PORT'])
