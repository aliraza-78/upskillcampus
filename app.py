from flask import Flask, render_template, request, redirect
import sqlite3
import string
import random
import re
from datetime import datetime

app = Flask(__name__)
DATABASE = "database.db"


# ------------------ DATABASE ------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            clicks INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# ------------------ SHORT CODE ------------------
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


# ------------------ VALIDATION ------------------
def is_valid_url(url):
    regex = re.compile(r'^(http|https)://')
    return re.match(regex, url)


# ------------------ HOME ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        original_url = request.form["url"]

        if not is_valid_url(original_url):
            return render_template("index.html", error="Invalid URL!")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("SELECT short_code FROM urls WHERE original_url = ?", (original_url,))
        result = cursor.fetchone()

        if result:
            short_code = result[0]
        else:
            short_code = generate_short_code()

            while True:
                cursor.execute("SELECT id FROM urls WHERE short_code = ?", (short_code,))
                if cursor.fetchone() is None:
                    break
                short_code = generate_short_code()

            cursor.execute(
                "INSERT INTO urls (original_url, short_code, created_at) VALUES (?, ?, ?)",
                (original_url, short_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()

        conn.close()

        short_url = request.host_url + short_code
        return render_template("result.html", short_url=short_url)

    return render_template("index.html")


# ------------------ REDIRECT ------------------
@app.route("/<short_code>")
def redirect_url(short_code):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT original_url, clicks FROM urls WHERE short_code = ?", (short_code,))
    result = cursor.fetchone()

    if result:
        original_url, clicks = result
        cursor.execute("UPDATE urls SET clicks = ? WHERE short_code = ?", (clicks + 1, short_code))
        conn.commit()
        conn.close()
        return redirect(original_url)
    else:
        conn.close()
        return "Invalid URL", 404


# ------------------ ANALYTICS ------------------
@app.route("/analytics")
def analytics():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT original_url, short_code, clicks FROM urls")
    data = cursor.fetchall()
    conn.close()
    return render_template("analytics.html", data=data)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
