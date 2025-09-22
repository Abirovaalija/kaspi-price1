from flask import Flask, Response
import requests
import csv
import io
import html
from datetime import datetime

app = Flask(__name__)

# --- ВАШИ НАСТРОЙКИ ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgYq1GLz1XNtMJHZFl75t81eciM-aqK8J7ugup0lfeAtBE8hWBmnaSKXYNcn1FXHgHOCu-axREC20m/pub?output=csv"
MERCHANT_ID = "30417165"   # ID магазина
COMPANY_NAME = "30417165"  # Можно оставить ID, либо название магазина
# ----------------------

@app.route("/")
def home():
    return "Сервер работает ✅  Данные: /price.xml"

@app.route("/price.xml")
def price_xml():
    # 1. Загружаем CSV
    r = requests.get(CSV_URL)
    r.encoding = "utf-8"
    reader = csv.DictReader(io.StringIO(r.text))

    # 2. Заголовок XML (строго по схеме Kaspi)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kaspi_catalog '
        'xmlns="kaspiShopping" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="kaspiShopping http://kaspi.kz/kaspishopping.xsd" '
        f'date="{datetime.now().strftime("%Y-%m-%d %H:%M")}">\n'
    )
    xml += f"  <company>{html.escape(COMPANY_NAME)}</company>\n"
    xml += f"  <merchantid>{MERCHANT_ID}</merchantid>\n"
    xml += "  <offers>\n"

    # 3. Товары
    for row in reader:
        sku   = html.escape(row.get("SKU","").strip())
        model = html.escape(row.get("model","").strip())
        brand = html.escape(row.get("brand","").strip())
        price = row.get("price","").strip()

        # пропускаем, если нет цены или SKU
        if not sku or not price.isdigit():
            continue

        # склады (PP1–PP5)
        stores_xml = ""
        for i in range(1,6):
            stock = row.get(f"PP{i}","").strip()
            preorder = row.get("preOrder","").strip() or "0"

            # проверяем, что stock — целое число
            if not stock.isdigit():
                continue

            available = "yes" if int(stock) > 0 else "no"
            stores_xml += (
                f'      <availability available="{available}" '
                f'storeId="{MERCHANT_ID}_PP{i}" '
                f'preOrder="{preorder}" '
                f'stockCount="{stock}"/>\n'
            )

        if not stores_xml:
            continue

        xml += f'    <offer sku="{sku}">\n'
        xml += f"      <model>{model}</model>\n"
        xml += f"      <brand>{brand}</brand>\n"
        xml += "      <availabilities>\n" + stores_xml + "      </availabilities>\n"
        xml += f"      <price>{price}</price>\n"
        xml += "    </offer>\n"

    # 4. Закрывающие теги
    xml += "  </offers>\n</kaspi_catalog>"

    return Response(xml, mimetype="application/xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
