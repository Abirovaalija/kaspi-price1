import csv
import requests
from flask import Flask, Response

app = Flask(__name__)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4ZELBB4oxdsdnCcZz-Svv4Jx2fuWxdLepdn1KuwtDUkNWkCf4FixqnREchgjgESOgGnAUReiL-KSF/pub?output=csv"

@app.route("/price.xml")
def price_xml():
    response = requests.get(CSV_URL)
    response.encoding = "utf-8"
    data = response.text.splitlines()

    reader = csv.DictReader(data)

    # Заголовок XML
    xml = '<?xml version="1.0" encoding="utf-8"?>\n'
    xml += '<kaspi_catalog date="2025-09-14" xmlns="kaspiShopping" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
    xml += f'  <company>30345911</company>\n'
    xml += f'  <merchantid>30345911</merchantid>\n'
    xml += '  <offers>\n'

    for row in reader:
        try:
            product_id = row.get("ID", "").strip()
            sku = row.get("SKU", "").strip()
            name = row.get("Наименование", "").strip()
            brand = row.get("Бренд", "").strip()
            price = row.get("Цена", "").strip()
            quantity = row.get("Количество", "").strip()
            city_availability = row.get("Доступность", "Уральск").strip()  # по умолчанию Уральск

            if not product_id or not price:
                continue  # пропускаем пустые строки

            xml += f'    <offer sku="{sku}">\n'
            xml += f'      <model>{name}</model>\n'
            xml += f'      <brand>{brand}</brand>\n'
            xml += f'      <price>{price}</price>\n'
            xml += f'      <quantity>{quantity if quantity else 1}</quantity>\n'
            xml += f'      <cityavailability>\n'
            xml += f'        <city id="750000000">Уральск</city>\n'
            xml += f'      </cityavailability>\n'
            xml += f'    </offer>\n'
        except Exception as e:
            print("Ошибка строки:", row, e)

    # Закрывающие теги
    xml += '  </offers>\n'
    xml += '</kaspi_catalog>\n'

    return Response(xml, mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
