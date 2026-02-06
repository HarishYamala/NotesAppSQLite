from flask import Flask, render_template, redirect, request, session, flash, url_for
import sqlite3
import os
import uuid
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from config import SECRET_KEY, MAIL_CONFIG

app = Flask(__name__)
app.secret_key = SECRET_KEY

# =========================
# Database Connection
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db_connection():
    conn = sqlite3.connect(os.path.join(BASE_DIR, "notes.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# =========================
# Routes
# =========================

@app.route("/")
def home():
    return redirect(url_for("viewall")) if "user_id" in session else redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
            flash("Registration successful", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email already exists", "danger")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful", "success")
            return redirect(url_for("viewall"))

        flash("Invalid credentials", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/viewall")
def viewall():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get("q", "")

    conn = get_db_connection()
    if search:
        notes = conn.execute("""
            SELECT * FROM notes
            WHERE user_id = ?
            AND (title LIKE ? OR content LIKE ?)
            ORDER BY created_at DESC
        """, (
            session["user_id"],
            f"%{search}%",
            f"%{search}%"
        )).fetchall()
    else:
        notes = conn.execute("""
            SELECT * FROM notes
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (session["user_id"],)).fetchall()

    conn.close()
    return render_template("viewnotes.html", notes=notes, search=search)


@app.route("/addnote", methods=["GET", "POST"])
def addnote():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)",
            (title, content, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Note added successfully", "success")
        return redirect(url_for("viewall"))

    return render_template("addnote.html")


@app.route("/view/<int:note_id>")
def view(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    note = conn.execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?",
        (note_id, session["user_id"])
    ).fetchone()
    conn.close()

    if not note:
        flash("Note not found", "danger")
        return redirect(url_for("viewall"))

    return render_template("singlenote.html", note=note)


@app.route("/update/<int:note_id>", methods=["GET", "POST"])
def update(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    note = conn.execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?",
        (note_id, session["user_id"])
    ).fetchone()

    if not note:
        conn.close()
        flash("Note not found", "danger")
        return redirect(url_for("viewall"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        conn.execute(
            "UPDATE notes SET title = ?, content = ? WHERE id = ? AND user_id = ?",
            (title, content, note_id, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Note updated", "success")
        return redirect(url_for("viewall"))

    conn.close()
    return render_template("updatenote.html", note=note)


@app.route("/delete/<int:note_id>", methods=["POST"])
def delete(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?",
        (note_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    flash("Note deleted", "info")
    return redirect(url_for("viewall"))

# =========================
# Forgot Password
# =========================

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":

        # 🔐 Safety check (prevents silent 500 errors)
        if not MAIL_CONFIG["MAIL_PASSWORD"]:
            raise RuntimeError(
                "MAIL_PASSWORD not set. Add it in PythonAnywhere → Web → Environment Variables."
            )

        email = request.form["email"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if not user:
            conn.close()
            flash("Email not found", "danger")
            return redirect(url_for("forgot"))

        token = str(uuid.uuid4())

        conn.execute(
            "UPDATE users SET reset_token = ? WHERE email = ?",
            (token, email)
        )
        conn.commit()
        conn.close()

        reset_link = url_for("reset", token=token, _external=True)

        msg = EmailMessage()
        msg.set_content(f"Click the link to reset your password:\n\n{reset_link}")
        msg["Subject"] = "Password Reset"
        msg["From"] = MAIL_CONFIG["MAIL_USERNAME"]
        msg["To"] = email

        with smtplib.SMTP_SSL(
            MAIL_CONFIG["MAIL_SERVER"],
            MAIL_CONFIG["MAIL_PORT"]
        ) as server:
            server.login(
                MAIL_CONFIG["MAIL_USERNAME"],
                MAIL_CONFIG["MAIL_PASSWORD"]
            )
            server.send_message(msg)

        flash("Password reset link sent to your email", "success")
        return redirect(url_for("login"))

    return render_template("forgot.html")

# =========================
# Reset Password
# =========================

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    conn = get_db_connection()

    user = conn.execute(
        "SELECT id FROM users WHERE reset_token = ?",
        (token,)
    ).fetchone()

    if not user:
        conn.close()
        flash("Invalid or expired reset link", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for("reset", token=token))

        hashed_password = generate_password_hash(password)

        conn.execute(
            "UPDATE users SET password = ?, reset_token = NULL WHERE reset_token = ?",
            (hashed_password, token)
        )
        conn.commit()
        conn.close()

        flash("Password updated successfully. Please login.", "success")
        return redirect(url_for("login"))

    conn.close()
    return render_template("reset.html", token=token)

# =========================
# Static Pages
# =========================

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")

# =========================
# Local Run (ignored by PythonAnywhere)
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
