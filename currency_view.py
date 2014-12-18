from flask import Response, jsonify, render_template
from lxml import etree
from currency import date_format


class CurrencyResponse:
    def __init__(self, price, date):
        self.price = price
        self.date = date

    def to_xml(self):
        root = etree.Element("currency")
        for k, v in self.price.items():
            etree.SubElement(root, k).text = str(v)

        xml = etree.tostring(root, pretty_print=True)
        return Response(xml, mimetype='application/xml')

    def to_json(self):
        return jsonify(self.price)

    def to_plain_text(self):
        txt = "Currency price on %s\n\n" % (self.date.strftime(date_format),)

        for k, v in self.price.items():
            txt += "%s cost %s roubles\n" % (k, v)

        return Response(txt, mimetype='text/plain')

    def to_html(self):
        return render_template("currency.html", date=self.date.strftime(date_format), price=self.price)
