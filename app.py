from flask import Flask, render_template, request, redirect, send_file
import sqlite3, datetime, os, urllib.parse
from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
import qrcode

app = Flask(__name__)

BASE_URL = "https://templates-4iru.onrender.com"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(BASE_DIR, "logo_circle.png")
SIGN = os.path.join(BASE_DIR, "signature.png")
STAMP = os.path.join(BASE_DIR, "stamp.png")
FONT_PATH = os.path.join(BASE_DIR, "Amiri-Regular.ttf")

pdfmetrics.registerFont(TTFont("Arabic", FONT_PATH))

def ar(txt):
    return get_display(arabic_reshaper.reshape(str(txt)))

# DB
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name TEXT,
        amount INTEGER,
        date TEXT,
        month TEXT,
        note TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# 🔥 BORDER مزدوج
def draw_border(canvas, doc):
    width, height = A5

    # border خارجي
    canvas.setLineWidth(3)
    canvas.rect(10, 10, width-20, height-20)

    # border داخلي
    canvas.setLineWidth(1)
    canvas.rect(15, 15, width-30, height-30)

# PDF
def create_pdf(id, name, amount):

    file = f"receipt_{id}.pdf"

    doc = SimpleDocTemplate(
        file,
        pagesize=A5,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    BLUE = colors.HexColor("#0A5F9E")
    GREEN = colors.HexColor("#00C853")

    style_ar = ParagraphStyle(name="arabic", fontName="Arabic", fontSize=11, alignment=2)
    style_title = ParagraphStyle(name="title", fontName="Arabic", fontSize=14, alignment=1)

    content = []

    # HEADER
    header = []

    if os.path.exists(LOGO):
        header.append(Image(LOGO, 60, 60))
    else:
        header.append("")

    header_text = [
        Paragraph(ar("أكاديمية أمل سوس لكرة القدم"), style_title),
        Spacer(1,5),
        Paragraph("Académie Amal Souss de Football", ParagraphStyle(name="fr", fontSize=10, alignment=1))
    ]

    header.append(header_text)

    content.append(Table([header], colWidths=[80, 300]))

    content.append(Spacer(1,10))
    content.append(Table([[""]], colWidths=[450], style=[
        ('LINEABOVE', (0,0), (-1,-1), 2, BLUE)
    ]))

    content.append(Spacer(1,15))

    # TABLE وسط
    data = [
        [ar("البيان"), ar("المعطيات")],
        [ar("اسم اللاعب"), ar(name)],
        [ar("المبلغ"), ar(f"{amount} درهم")],
        [ar("التاريخ"), ar(str(datetime.date.today()))]
    ]

    table = Table(data, colWidths=[180, 220])

    table.setStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT')
    ])

    content.append(Spacer(1,25))
    content.append(table)
    content.append(Spacer(1,30))

    # QR
    try:
        link = f"{BASE_URL}/pdf/{id}"
        qr_file = f"qr_{id}.png"
        qrcode.make(link).save(qr_file)
        content.append(Image(qr_file, 90, 90))
    except:
        pass

    content.append(Spacer(1,20))

    # SIGN + STAMP
    row = []

    if os.path.exists(SIGN):
        row.append(Image(SIGN, 120, 50))
    else:
        row.append("")

    if os.path.exists(STAMP):
        row.append(Image(STAMP, 100, 100))
    else:
        row.append("")

    content.append(Table([row], colWidths=[200, 200]))

    content.append(Spacer(1,20))

    # FOOTER
    content.append(Table([[""]], colWidths=[450], style=[
        ('LINEABOVE', (0,0), (-1,-1), 2, GREEN)
    ]))

    content.append(Spacer(1,10))

    content.append(Paragraph(ar("أكاديمية أمل سوس لكرة القدم"), style_ar))
    content.append(Paragraph(ar("المقر: شارع الادارسة زنقة 3101 رقم 76 الدشيرة الجهادية"), style_ar))
    content.append(Paragraph(ar("الهاتف: 06 31 61 66 67 / 06 87 89 51 63"), style_ar))

    doc.build(content, onFirstPage=draw_border, onLaterPages=draw_border)

    return file

# ROUTES
@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        amount = int(request.form["amount"])
        month = request.form["month"]
        note = request.form["note"]
        date = datetime.date.today()

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO payments VALUES (NULL, ?, ?, ?, ?, ?)",
                  (name, amount, date, month, note))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT SUM(amount) FROM payments")
    total = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(DISTINCT player_name) FROM payments")
    players = c.fetchone()[0]

    c.execute("SELECT * FROM payments ORDER BY id DESC")
    rows = c.fetchall()

    conn.close()

    return render_template("dashboard.html", total=total, players=players, rows=rows)

@app.route("/pdf/<int:id>")
def pdf(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM payments WHERE id=?", (id,))
    r = c.fetchone()
    conn.close()

    file = create_pdf(id, r[1], r[2])
    return send_file(file, as_attachment=True)

@app.route("/whatsapp/<int:id>")
def whatsapp(id):
    link = f"{BASE_URL}/pdf/{id}"
    msg = f"وصل الأداء:\n{link}"
    url = "https://wa.me/?text=" + urllib.parse.quote(msg)
    return redirect(url)

@app.route("/search", methods=["GET","POST"])
def search():
    results = []
    if request.method == "POST":
        name = request.form["name"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM payments WHERE player_name LIKE ?", ('%' + name + '%',))
        results = c.fetchall()
        conn.close()

    return render_template("search.html", results=results)

# Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
