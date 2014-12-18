from flask import g
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing

def connect_db():
    rv = sqlite3.connect(g.app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    with closing(connect_db()) as db:
        with g.app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db


def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()
