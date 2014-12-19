import requests
from bs4 import BeautifulSoup
from datetime import datetime

currency_codes = {'USD': 'R01235', 'Euro': 'R01239'}
date_format = "%d/%m/%Y"


def get_currency_price(date):
    date = ensure_str(date)

    url = "http://www.cbr.ru/scripts/XML_daily.asp"
    request = requests.get(url, params={'date_req': date})
    request.raise_for_status()
    soup = BeautifulSoup(request.text)

    if not check_date(soup, date):
        return None

    res = {}
    for char_code, cur_id in currency_codes.items():
        tag = soup.find(id=cur_id)
        if tag is None or tag.value is None:
            return None

        res[char_code] = float(tag.value.string.replace(',', '.'))

    return res


def check_date(soup, expected):
    got_curs = soup.find('valcurs')
    if got_curs is None:
        return None
    got = got_curs['date']

    try:
        try:
            got = datetime.strptime(got, "%d.%m.%Y")
            got = ensure_str(got)
        except ValueError:
            pass
        expected = ensure_str(expected)

        return got == expected
    except ValueError:
        return False


def get_price_range(date_from, date_to, cur_id):
    data = {}
    data['date_req1'] = ensure_str(date_from)
    data['date_req2'] = ensure_str(date_to)
    data['VAL_NM_RQ'] = currency_codes[cur_id]

    url = "http://www.cbr.ru/scripts/XML_dynamic.asp"
    request = requests.get(url, params=data)
    request.raise_for_status()
    soup = BeautifulSoup(request.text)

    res = {}
    for tag in soup.find_all("record"):
        day = tag['date']
        val = float(tag.value.string.replace(',', '.'))
        res[day] = val

    return res


def ensure_str(date):
    if not isinstance(date, (str, unicode)):
        date = date.strftime(date_format)
    return date

