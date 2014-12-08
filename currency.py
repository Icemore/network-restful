import requests
from bs4 import BeautifulSoup


currency_codes = {'USD': 'R01235', 'Euro': 'R01239'}
date_format = "%d/%m/%Y"


def get_currency_price(date):
    return {'USD': 34.23, 'Euro': 40.50}

    date = ensure_str(date)

    url = "http://www.cbr.ru/scripts/XML_daily.asp"
    request = requests.get(url, params={'date_req': date})
    request.raise_for_status()
    soup = BeautifulSoup(request.text)

    res = {}
    for char_code, cur_id in currency_codes.items():
        tag = soup.find(id=cur_id)
        if tag is None or tag.value is None:
            raise ValueError()

        res[char_code] = float(tag.value.string.replace(',', '.'))

    return res


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

