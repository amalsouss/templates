from flask import Flask, render_template, request, redirect, send_file
import sqlite3, datetime, os, urllib.parse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
import qrcode

app = Flask(__name__)

BASE_URL = "https://academy-app-lco1.onrender.com"

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

# PDF
def create_pdf(name, amount):
    file = "receipt.pdf"
    doc = SimpleDocTemplate(file, pagesize=A5)
    style = ParagraphStyle(name="normal", fontSize=12)

    data = [
        ["الاسم", name],
        ["المبلغ", f"{amount} درهم"]
    ]

    content = [Paragraph("وصل الأداء", style), Table(data)]
    doc.build(content)

    return file

# HOME
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

# DASHBOARD
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

# PDF
@app.route("/pdf/<int:id>")
def pdf(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM payments WHERE id=?", (id,))
    r = c.fetchone()
    conn.close()

    file = create_pdf(r[1], r[2])
    return send_file(file, as_attachment=True)

# WhatsApp
@app.route("/whatsapp/<int:id>")
def whatsapp(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM payments WHERE id=?", (id,))
    r = c.fetchone()
    conn.close()

    link = f"{BASE_URL}/pdf/{id}"

    msg = f"وصل الأداء:\n{r[1]}\n{r[2]} درهم\n{link}"
    url = "https://wa.me/?text=" + urllib.parse.quote(msg)

    return redirect(url)

# SEARCH
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
    app.run()
