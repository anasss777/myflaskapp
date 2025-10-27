from flask import Flask, send_file, jsonify
import mysql.connector
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
from dotenv import load_dotenv
import os
import tempfile

app = Flask(__name__)
load_dotenv()

def generate_pdf():
    hostName = os.getenv("MYSQL_DB_HOST")
    username = os.getenv("MYSQL_DB_USER")
    password = os.getenv("MYSQL_DB_PASSWORD")
    dbName = os.getenv("MYSQL_DB_NAME")

    db = mysql.connector.connect(
        host=hostName,
        user=username,
        password=password,
        database=dbName,
    )
    cursor = db.cursor()

    cursor.execute("""
    SELECT
        customers.name,
        customers.phone,
        customers.insta,
        customers.insta_followers,
        customers.priority,
        COUNT(DISTINCT contracts.id) AS rents,
        customers.address,
        customers.nat
    FROM customers
    LEFT JOIN contracts ON customers.id = contracts.customer_id
    JOIN contracts_items ON contracts.id = contracts_items.contract_id
    LEFT JOIN items_details ON contracts_items.item_details_id = items_details.id
    WHERE items_details.type = "rent" AND contracts.number NOT LIKE "QUOT%"
    GROUP BY
        customers.id,
        customers.name,
        customers.phone,
        customers.insta,
        customers.insta_followers,
        customers.priority,
        customers.address,
        customers.nat
    ORDER BY rents DESC, insta_followers DESC, priority;
    """)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    db.close()

    # Save PDF in a temp file
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_file = temp_pdf.name

    pdfmetrics.registerFont(TTFont("Arabic", "fonts/NotoNaskhArabic-Regular.ttf"))
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)

    def reshape_text(text):
        try:
            reshaped = arabic_reshaper.reshape(str(text))
            bidi_text = get_display(reshaped)
            return bidi_text
        except:
            return str(text)

    reshaped_rows = [[reshape_text(cell) for cell in row] for row in rows]
    reshaped_columns = [reshape_text(col) for col in columns]
    data = [reshaped_columns] + reshaped_rows

    col_widths = [160, 50, 100, 40, 40, 15, 160, 60]
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.gray),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,-1), "Arabic"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,0), 12),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,1), (-1,-1), colors.beige)
    ]))

    elements = [Paragraph("قائمة العملاء (Event Customers)", styles["Title"]), table]
    doc.build(elements)
    return pdf_file


@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Event Customers PDF API!"})


@app.route("/generate_pdf", methods=["GET"])
def generate_pdf_route():
    try:
        pdf_path = generate_pdf()
        return send_file(pdf_path, as_attachment=True, download_name="eventCustomersByRents.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
