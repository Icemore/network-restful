from flask.views import MethodView
from flask import Response, jsonify, render_template, abort
from lxml import etree
from task_operations import *
from currency import get_price_range, date_format
from content_parsing import respond, get_request_data
from datetime import datetime

class TaskView(MethodView):
    def get_task_or_die(self, task_id):
        task = get_task(task_id)
        if task is None:
            abort(404)
        return task

    def get(self, task_id):
        if task_id is None:
            # return list of all tasks
            return respond(AllTasksResponse(get_all_tasks()))

        task = self.get_task_or_die(task_id)
        data = get_price_range(task['date_from'], task['date_to'], task['cur_id'])

        return respond(TaskResponse(task, data))

    def delete(self, task_id):
        self.get_task_or_die(task_id)

        if delete_task(task_id):
            return "OK"
        else:
            abort(500)

    def post(self, task_id):
        self.get_task_or_die(task_id)
        data = get_request_data(require_all=False)

        if update_task(task_id, data):
            return "OK"
        else:
            abort(500)

    def put(self):
        data = get_request_data(require_all=True)
        task_id = add_task(data)

        return respond(TaskIdResponse(task_id))


class TaskResponse:
    def __init__(self, task, data):
        self.task = task
        self.data = data
        self.sorted_data = sorted(data.items(), key=lambda (k, v): datetime.strptime(k, "%d.%m.%Y"))

    def to_xml(self):
        root = etree.Element("history")
        for k, v in self.sorted_data:
            etree.SubElement(root, "record", date=k).text = str(v)

        xml = etree.tostring(root, pretty_print=True)
        return Response(xml, mimetype='application/xml')

    def to_json(self):
        return jsonify(self.data)

    def to_plain_text(self):
        txt = "Prices of %s from %s to %s\n\n" % (self.task['cur_id'],
                                                  self.task['date_from'],
                                                  self.task['date_to'])

        for k, v in self.sorted_data:
            txt += "%s %s rub\n" % (k, v)

        return Response(txt, mimetype='text/plain')

    def to_html(self):
        return render_template("task.html", task=self.task, data=self.sorted_data)

class TaskIdResponse:
    def __init__(self, task_id):
        self.task_id = task_id

    def to_xml(self):
        root = etree.Element("task_id").text = str(self.task_id)
        xml = etree.tostring(root, pretty_print=True)
        return Response(xml, mimetype='application/xml')

    def to_json(self):
        return jsonify({'task_id': self.task_id})

    def to_plain_text(self):
        return str(self.task_id)

    def to_html(self):
        return str(self.task_id)


class AllTasksResponse:
    def __init__(self, tasks):
        self.tasks = tasks

    def to_xml(self):
        root = etree.Element("task_list")
        for task in self.tasks:
            cur = etree.SubElement(root, "task", id=str(task['id']))

            for attr in ['date_from', 'date_to', 'cur_id']:
                etree.SubElement(cur, attr).text = str(task[attr])

        xml = etree.tostring(root, pretty_print=True)
        return Response(xml, mimetype='application/xml')

    def to_json(self):
        json = {}
        for task in self.tasks:
            json[task['id']] = {
                'date_from': task['date_from'],
                'date_to': task['date_to'],
                'cur_id': task['cur_id']
            }
        return jsonify(json)

    def to_plain_text(self):
        text = "Active tasks\n\n"

        for task in self.tasks:
            text += "id: {}, from: {}, to: {}, currency: {}\n".format(
                task['id'], task['date_from'], task['date_to'], task['cur_id'])

        return Response(text, mimetype='text/plain')

    def to_html(self):
        return render_template("tasks.html", tasks=self.tasks)
