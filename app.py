# from flask import Flask, send_file, jsonify
# import mysql.connector
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# import arabic_reshaper
# from bidi.algorithm import get_display
# from dotenv import load_dotenv
# import os
# import threading
# import uuid

# app = Flask(__name__)
# load_dotenv()

# # Folder to store generated PDFs
# PDF_FOLDER = os.path.join(os.path.dirname(__file__), "generated_pdfs")
# os.makedirs(PDF_FOLDER, exist_ok=True)

# # In-memory job tracker (for demo; in production, use DB or Redis)
# jobs = {}

# # Register Arabic font
# FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "NotoNaskhArabic-Regular.ttf")
# pdfmetrics.registerFont(TTFont("Arabic", FONT_PATH))

# def reshape_text(text):
#     try:
#         reshaped = arabic_reshaper.reshape(str(text))
#         bidi_text = get_display(reshaped)
#         return bidi_text
#     except:
#         return str(text)

# def generate_pdf_file(job_id):
#     """Background PDF generator."""
#     try:
#         hostName = os.getenv("MYSQL_DB_HOST")
#         username = os.getenv("MYSQL_DB_USER")
#         password = os.getenv("MYSQL_DB_PASSWORD")
#         dbName = os.getenv("MYSQL_DB_NAME")

#         db = mysql.connector.connect(
#             host=hostName,
#             user=username,
#             password=password,
#             database=dbName,
#         )
#         cursor = db.cursor()

#         cursor.execute("""
#         SELECT
#             customers.name,
#             customers.phone,
#             customers.insta,
#             customers.insta_followers,
#             customers.priority,
#             COUNT(DISTINCT contracts.id) AS rents,
#             customers.address,
#             customers.nat
#         FROM customers
#         LEFT JOIN contracts ON customers.id = contracts.customer_id
#         JOIN contracts_items ON contracts.id = contracts_items.contract_id
#         LEFT JOIN items_details ON contracts_items.item_details_id = items_details.id
#         WHERE items_details.type = "rent" AND contracts.number NOT LIKE "QUOT%"
#         GROUP BY
#             customers.id,
#             customers.name,
#             customers.phone,
#             customers.insta,
#             customers.insta_followers,
#             customers.priority,
#             customers.address,
#             customers.nat
#         ORDER BY rents DESC, insta_followers DESC, priority;
#         """)
#         rows = cursor.fetchall()
#         columns = [desc[0] for desc in cursor.description]
#         db.close()

#         pdf_path = os.path.join(PDF_FOLDER, f"{job_id}.pdf")
#         doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)

#         reshaped_rows = [[reshape_text(cell) for cell in row] for row in rows]
#         reshaped_columns = [reshape_text(col) for col in columns]
#         data = [reshaped_columns] + reshaped_rows

#         col_widths = [160, 50, 100, 40, 40, 15, 160, 60]
#         table = Table(data, colWidths=col_widths)
#         table.setStyle(TableStyle([
#             ("BACKGROUND", (0,0), (-1,0), colors.gray),
#             ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
#             ("ALIGN", (0,0), (-1,-1), "CENTER"),
#             ("FONTNAME", (0,0), (-1,-1), "Arabic"),
#             ("FONTSIZE", (0,0), (-1,-1), 9),
#             ("BOTTOMPADDING", (0,0), (-1,0), 12),
#             ("GRID", (0,0), (-1,-1), 0.5, colors.black),
#             ("BACKGROUND", (0,1), (-1,-1), colors.beige)
#         ]))

#         elements = [Paragraph("قائمة العملاء (Event Customers)", getSampleStyleSheet()["Title"]), table]
#         doc.build(elements)

#         jobs[job_id]["status"] = "done"
#         jobs[job_id]["file"] = pdf_path

#     except Exception as e:
#         jobs[job_id]["status"] = "failed"
#         jobs[job_id]["error"] = str(e)


# @app.route("/")
# def home():
#     return jsonify({"message": "Welcome to the Event Customers PDF API!"})


# @app.route("/generate_pdf", methods=["GET"])
# def generate_pdf_route():
#     job_id = str(uuid.uuid4())
#     jobs[job_id] = {"status": "processing", "file": None}
#     thread = threading.Thread(target=generate_pdf_file, args=(job_id,))
#     thread.start()
#     return jsonify({"job_id": job_id, "status": "processing"})


# @app.route("/download_pdf/<job_id>", methods=["GET"])
# def download_pdf_route(job_id):
#     job = jobs.get(job_id)
#     if not job:
#         return jsonify({"error": "Job ID not found"}), 404
#     if job["status"] == "processing":
#         return jsonify({"status": "processing"}), 202
#     if job["status"] == "failed":
#         return jsonify({"status": "failed", "error": job.get("error")}), 500
#     return send_file(job["file"], as_attachment=True, download_name="eventCustomersByRents.pdf")


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)

from flask import Flask, send_file, jsonify
import mysql.connector
import csv
import os
from dotenv import load_dotenv
import tempfile

app = Flask(__name__)
load_dotenv()

def generate_csv():
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

    # Create a temp CSV file
    temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w', newline='', encoding='utf-8-sig')
    csv_file = temp_csv.name

    writer = csv.writer(temp_csv)
    writer.writerow(columns)  # header
    writer.writerows(rows)    # data
    temp_csv.close()
    return csv_file

@app.route("/generate_csv", methods=["GET"])
def generate_csv_route():
    try:
        csv_path = generate_csv()
        return send_file(csv_path, as_attachment=True, download_name="eventCustomersByRents.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Event Customers CSV API!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
