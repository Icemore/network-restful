from flask import request, abort
from bs4 import BeautifulSoup
from datetime import datetime
from currency import date_format, currency_codes


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
    if request.content_type == 'application/xml':
        data = parse_xml()
    elif request.content_type == 'application/json':
        data = parse_json()
    elif request.content_type == 'application/x-www-form-urlencoded':
        data = parse_http()
    else:
        abort(405)

    fail = False
    for date_attr in ['date_from', 'date_to']:
        if date_attr in data:
            try:
                datetime.strptime(data[date_attr], date_format)
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


def get_expected_type():
    default = 'text/html'
    acceptable = ['application/json', 'application/xml',
                  'text/plain', default]

    best = request.accept_mimetypes.best_match(acceptable)

    if best is None:
        abort(406)

    if request.accept_mimetypes[best] <= request.accept_mimetypes[default]:
        return default
    else:
        return best


def respond(res):
    best_type = get_expected_type()

    if best_type.endswith('json'):
        return res.to_json()
    elif best_type.endswith('xml'):
        return res.to_xml()
    elif best_type == "text/plain":
        return res.to_plain_text()
    else:
        return res.to_html()
