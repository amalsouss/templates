from flask import Flask, render_template, request, redirect, send_file
import sqlite3, datetime, os, urllib.parse
from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
import qrcode

app = Flask(__name__)

BASE_URL = "https://templates-4iru.onrender.com"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(BASE_DIR, "logo_circle.png")
SIGN = os.path.join(BASE_DIR, "signature.png")
STAMP = os.path.join(BASE_DIR, "stamp.png")

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

# BORDER
def draw_border(canvas, doc):
    width, height = A5
    canvas.setLineWidth(3)
    canvas.rect(10, 10, width-20, height-20)
    canvas.setLineWidth(1)
    canvas.rect(15, 15, width-30, height-30)

# PDF
def create_pdf(id, name, amount):

    file = f"receipt_{id}.pdf"

    doc = SimpleDocTemplate(file, pagesize=A5)

    content = []

    # HEADER
    content.append(Paragraph("Academie Amal Souss de Football"))
    content.append(Spacer(1,10))

    # TABLE
    data = [
        ["Name", name],
        ["Amount", f"{amount} MAD"],
        ["Date", str(datetime.date.today())]
    ]

    table = Table(data)
    table.setStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])

    content.append(table)
    content.append(Spacer(1,20))

    # QR
    try:
        link = f"{BASE_URL}/pdf/{id}"
        qr_file = f"qr_{id}.png"
        qrcode.make(link).save(qr_file)
        content.append(Image(qr_file, 80, 80))
    except:
        pass

    doc.build(content, onFirstPage=draw_border)

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
    msg = f"Payment receipt:\n{link}"
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
