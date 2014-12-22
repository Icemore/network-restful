import logging
from logging.handlers import RotatingFileHandler
import os

from flask import Flask, abort, render_template, send_file, request
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
    PORT=80,
    LOG_FILENAME='logs.log'
))
app.teardown_appcontext_funcs.append(close_db)

@app.before_first_request
def setup_logging():
    app.logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        app.config['LOG_FILENAME'],
        maxBytes=1024 * 1024 * 100
        )

    app.logger.addHandler(handler)

@app.before_request
def pre_request_logging():
    app.logger.info('\t'.join([
        datetime.today().ctime(),
        request.remote_addr,
        request.method,
        request.url,
        request.data,
        ', '.join([': '.join(x) for x in request.headers])])
    )

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/logs')
def logs():
    return send_file(app.config['LOG_FILENAME'], mimetype='text/plain')

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
