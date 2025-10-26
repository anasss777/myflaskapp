import mysql.connector
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

# ----------------------------
# 1. Database connection
# ----------------------------
db = mysql.connector.connect(
    host= "162.240.170.82",
    user= "lurencompany_halaDD",
    password= "Pi314159*",
    database= "lurencompany_halaDDdb",
)
cursor = db.cursor()

# ----------------------------
# 2. Fetch data
# ----------------------------
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
GROUP BY
    customers.id,
    customers.name,
    customers.phone,
    customers.insta,
    customers.insta_followers,
    customers.priority,
    customers.address,
    customers.nat
ORDER BY rents DESC, insta_followers DESC, priority;""")
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

# ----------------------------
# 3. Setup PDF
# ----------------------------
pdf_file = "eventCustomersByRents.pdf"
doc = SimpleDocTemplate(pdf_file, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
styles = getSampleStyleSheet()

# Register Arabic font (you can change this to any Arabic TTF file on your system)
pdfmetrics.registerFont(TTFont("Arabic", "arial.ttf"))

def reshape_text(text):
    """Reshape Arabic text for proper display."""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped)
        return bidi_text
    except:
        return str(text)

# ----------------------------
# 4. Prepare table data
# ----------------------------
# Reshape each cell (in case of Arabic)
reshaped_rows = []
for row in rows:
    reshaped_rows.append([reshape_text(cell) for cell in row])

reshaped_columns = [reshape_text(col) for col in columns]
data = [reshaped_columns] + reshaped_rows

# ----------------------------
# 5. Table styling
# ----------------------------
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

# ----------------------------
# 6. Build PDF
# ----------------------------
doc.build(elements)

print(f"✅ Arabic-friendly PDF saved as {pdf_file}")
