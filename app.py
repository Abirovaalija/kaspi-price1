import csv
import html
import requests
from datetime import datetime
from flask import Flask, Response

app = Flask(__name__)

# === НАСТРОЙКИ ===
GOOGLE_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTgYq1GLz1XNtMJHZFl75t81eciM-aqK8J7ugup0lfeAtBE8hWBmnaSKXYNcn1FXHgHOCu-axREC20m/pub?output=csv"
)
MERCHANT_ID = "30417165"


def fetch_rows():
    """Загружает строки из Google Sheets CSV."""
    r = requests.get(GOOGLE_CSV_URL, timeout=30)
    r.raise_for_status()
    text = r.text.splitlines()
    reader = csv.DictReader(text)

    rows = []
    for row in reader:
        # Проверяем обязательные поля
        sku = row.get("SKU", "").strip()
        price = row.get("price", "").strip()
        if not sku or not price:
            continue  # пропускаем пустые

        # Получаем количество по складам
        stores = []
        for i in range(1, 6):
            qty = row.get(f"PP{i}", "").strip()
            # если пусто — 0
            qty = int(qty) if qty.isdigit() else 0
            stores.append(qty)

        pre_order = row.get("preOrder", "").strip()
        pre_order = int(pre_order) if pre_order.isdigit() else 0

        rows.append({
            "sku": sku,
            "model": html.escape(row.get("model", "").strip()),
            "brand": html.escape(row.get("brand", "").strip() or "Без бренда"),
            "price": int(price),
            "stores": stores,
            "pre_order": pre_order
        })
    return rows


@app.route("/price.xml")
def price_xml():
    rows = fetch_rows()
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    xml = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<kaspi_catalog xmlns="http://kaspi.kz/kaspishopping.xsd" '
        f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        f'xsi:schemaLocation="http://kaspi.kz/kaspishopping.xsd" '
        f'date="{today}">',
        f'  <company>{MERCHANT_ID}</company>',
        f'  <merchantid>{MERCHANT_ID}</merchantid>',
        "  <offers>"
    ]

    for r in rows:
        xml.append(f'    <offer sku="{r["sku"]}">')
        xml.append(f'      <model>{r["model"]}</model>')
        xml.append(f'      <brand>{r["brand"]}</brand>')
        xml.append("      <availabilities>")
        for i, qty in enumerate(r["stores"], start=1):
            available = "yes" if qty > 0 else "no"
            xml.append(
                f'        <availability available="{available}" '
                f'storeId="{MERCHANT_ID}_PP{i}" '
                f'preOrder="{r["pre_order"]}" '
                f'stockCount="{qty}"/>'
            )
        xml.append("      </availabilities>")
        xml.append(f'      <price>{r["price"]}</price>')
        xml.append("    </offer>")

    xml.append("  </offers>")
    xml.append("</kaspi_catalog>")

    return Response("\n".join(xml), mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
