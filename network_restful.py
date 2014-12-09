from flask import Flask, abort, jsonify, request, Response, render_template, g
from sqlite3 import dbapi2 as sqlite3
from datetime import datetime
from lxml import etree
from currency import *
from contextlib import closing
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

import os

app = Flask(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'currency.db'),
    DEBUG=False,
    HOST="0.0.0.0",
    PORT=80
))


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/')
def hello_world():
    return render_template("index.html")


@app.route('/currency/<path:date>')
def currency(date):
    try:
        date = datetime.strptime(date, date_format)
        res = get_currency_price(date)

        if request.headers['Accept'] == 'text/plain':
            return to_plain_text(date, res)
        elif request.headers['Accept'] == 'application/json':
            return jsonify(res)
        elif request.headers['Accept'] == 'application/xml' or \
                        request.headers['Accept'] == 'text/xml':
            return to_xml(res)
        else:
            return render_template("currency.html", date=date.strftime(date_format), price=res)

    except ValueError:
        abort(400)
    except HTTPError:
        abort(502)


@app.route('/tasks', methods=['GET', 'PUT'])
def tasks():
    if request.method == 'PUT':
        data = get_request_data(require_all=True)
        id = add_task(data)

        if request.headers['Accept'] == 'text/plain':
            return str(id)
        elif request.headers['Accept'] == 'application/json':
            return jsonify({'task_id': id})
        elif request.headers['Accept'] == 'application/xml' or \
                request.headers['Accept'] == 'text/xml':
            return id_to_xml(id)
        else:
            return str(id)

    return render_template("tasks.html", tasks=get_all_tasks())


def get_all_tasks():
    db = get_db()
    cur = db.execute("SELECT id, date_from, date_to, cur_id FROM tasks")
    return cur.fetchall()


@app.route('/tasks/<int:id>', methods=['GET', 'DELETE', 'POST'])
def task(id):
    task = get_task(id)
    if task is None:
        abort(404)

    if request.method == 'GET':
        data = get_price_range(task['date_from'], task['date_to'], task['cur_id'])

        if request.headers['Accept'] == 'text/plain':
            return task_to_plain_text(task, data)
        elif request.headers['Accept'] == 'application/json':
            return jsonify(data)
        elif request.headers['Accept'] == 'application/xml' or \
                request.headers['Accept'] == 'text/xml':
            return task_to_xml(task, data)
        else:
            return render_template("task.html", task=task, data=data)
    elif request.method == 'DELETE':
        if delete_task(id):
            return "OK"
        else:
            abort(500)
    elif request.method == 'POST':
        data = get_request_data(require_all=False)

        if update_task(id, data):
            return "OK"
        else:
            abort(500)


def parse_http():
    params = ['date_from', 'date_to', 'cur_id']
    res = {}
    for p in params:
        if p in request.values:
            res[p] = request.values[p]
    return res


def parse_xml():
    soup = BeautifulSoup(request.get_data())
    if soup.task is None:
        abort(400)

    res = {}
    for tag in soup.task.find_all():
        key = tag.name
        val = tag.text
        res[key] = val

    return res


def parse_json():
    return request.json


def get_request_data(require_all):
    if request.headers['Content-Type'].endswith('xml'):
        data = parse_xml()
    elif request.headers['Content-Type'].endswith('json'):
        data = parse_json()
    else:
        data = parse_http()

    fail = False
    for date_attr in ['date_from', 'date_to']:
        if date_attr in data:
            try:
                tmp = datetime.strptime(data[date_attr], date_format)
            except ValueError:
                fail = True
        else:
            fail = fail or require_all

    if 'cur_id' in data:
        if data['cur_id'] not in currency_codes:
            fail = True
    else:
        fail = fail or require_all

    if fail:
        abort(400)

    return data


def update_task(id, data):
    task = get_task(id)

    record = {'id': task['id']}
    for attr in ['date_from', 'date_to', 'cur_id']:
        if attr in data:
            record[attr] = data[attr]
        else:
            record[attr] = task[attr]

    db = get_db()
    cur = db.execute("UPDATE tasks SET date_from = ?, date_to = ?, cur_id = ? WHERE id = ?",
                     [record['date_from'], record['date_to'], record['cur_id'], record['id']])
    db.commit()
    return cur.rowcount == 1


def get_task(id):
    db = get_db()
    cur = db.execute("SELECT id, date_from, date_to, cur_id FROM tasks WHERE id = ?", [id])
    task = cur.fetchone()
    return task


def delete_task(id):
    db = get_db()
    cur = db.execute("DELETE FROM tasks WHERE id = ?", [id])
    db.commit()
    return cur.rowcount == 1


def add_task(data):
    db = get_db()

    cur = db.execute("INSERT INTO tasks (date_from, date_to, cur_id) VALUES (?, ?, ?)",
                     [data['date_from'], data['date_to'], data['cur_id']])
    db.commit()

    return cur.lastrowid


def to_plain_text(date, price):
    txt = "Currency price on %s\n\n" % (date.strftime(date_format),)

    for k, v in price.items():
        txt += "%s cost %s roubles\n" % (k, v)

    return Response(txt, mimetype='text/plain')


def task_to_plain_text(task, data):
    txt = "Prices of %s from %s to %s\n\n" % (task['cur_id'], task['date_from'], task['date_to'])

    for k, v in data.items():
        txt += "%s %s rub\n" % (k, v)

    return Response(txt, mimetype='text/plain')


def to_xml(price):
    root = etree.Element("currency")
    for k, v in price.items():
        etree.SubElement(root, k).text = v

    xml = etree.tostring(root, pretty_print=True)
    return Response(xml, mimetype='text/xml')


def task_to_xml(task, data):
    root = etree.Element("history")
    for k, v in data.items():
        etree.SubElement(root, "record", date=k).text = str(v)

    xml = etree.tostring(root, pretty_print=True)
    return Response(xml, mimetype='text/xml')


def id_to_xml(id):
    root = etree.Element("task_id").text = str(id)
    xml = etree.tostring(root, pretty_print=True)
    return Response(xml, mimetype='text/xml')


if __name__ == '__main__':
    app.run(host=app.config['HOST'], debug=app.config['DEBUG'], port=app.config['PORT'])
