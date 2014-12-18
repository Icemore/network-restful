from db import get_db


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


def get_all_tasks():
    db = get_db()
    cur = db.execute("SELECT id, date_from, date_to, cur_id FROM tasks")
    return cur.fetchall()
