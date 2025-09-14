from flask import Flask, Response
import requests, csv, io
import html
from datetime import datetime

app = Flask(__name__)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4ZELBB4oxdsdnCcZz-Svv4Jx2fuWxdLepdn1KuwtDUkNWkCf4FixqnREchgjgESOgGnAUReiL-KSF/pub?output=csv"
MERCHANT_ID = "30345911"

@app.route('/price.xml')
def price_xml():
    resp = requests.get(CSV_URL)
    resp.encoding = 'utf-8'
    csv_text = resp.text

    # Лог для проверки: первые 500 символов CSV
    print("=== CSV начало ===")
    print(csv_text[:500])
    print("=== Конец начала CSV ===")

    reader = csv.DictReader(io.StringIO(csv_text))

    # Формируем XML
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += f'<kaspi_catalog xmlns="kaspiShopping" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://kaspi.kz/kaspishopping.xsd" date="{date_now}">\n'
    xml += f'  <company>{MERCHANT_ID}</company>\n'
    xml += f'  <merchantid>{MERCHANT_ID}</merchantid>\n'
    xml += '  <offers>\n'

    rows_count = 0
    offers_count = 0

    for row in reader:
        rows_count += 1

        sku = html.escape(row.get("SKU", "").strip())
        model = html.escape(row.get("model", "").strip())
        brand = html.escape(row.get("brand", "").strip())
        price = row.get("price", "").strip() or "0"
        preorder = row.get("preorder", "").strip() or "0"

        # лог: какой sku и модель
        print(f"Row {rows_count}: SKU='{sku}' model='{model}' price='{price}' preorder='{preorder}'")

        # формируем availabilities
        availabilities = []
        for i in range(1, 6):
            stock_raw = row.get(f"PP{i}", "").strip()
            stock_count = stock_raw if stock_raw.isdigit() else "0"

            available = "yes" if stock_raw.isdigit() and int(stock_raw) > 0 else "no"

            store_id = f"{MERCHANT_ID}_PP{i}"
            availabilities.append(
                f'<availability available="{available}" storeId="{store_id}" preOrder="{preorder}" stockCount="{stock_count}"/>'
            )

        # проверка, есть ли предложение (хотя бы один available=yes и price > 0)
        if price != "0":
            offers_count += 1
            xml += f'    <offer sku="{sku}">\n'
            xml += f'      <model>{model}</model>\n'
            xml += f'      <brand>{brand}</brand>\n'
            xml += f'      <availabilities>\n'
            xml += "      " + "\n      ".join(availabilities) + "\n"
            xml += f'      </availabilities>\n'
            xml += f'      <price>{price}</price>\n'
            xml += f'    </offer>\n'

    xml += '  </offers>\n</kaspi_catalog>\n'

    print(f"Всего строк в CSV: {rows_count}, предложений (offers): {offers_count}")

    return Response(xml, mimetype='application/xml')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
