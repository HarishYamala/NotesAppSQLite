from flask import Flask, render_template, redirect, request, session, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from email.message import EmailMessage
import smtplib
import uuid
from config import SECRET_KEY, MAIL_CONFIG

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Database Connection Helper(SQLite) 

def get_db_connection():

    """
    Creates and Returns a SQLite database connection
    row_factory allows column access using names like dict 
    """
    conn=sqlite3.connect("notes.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("viewall"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
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

    if note is None:
        flash("Note not found", "danger")
        return redirect(url_for("viewall"))

    return render_template("singlenote.html", note=note)


@app.route("/update/<int:note_id>", methods=["GET", "POST"])
def update(note_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    # Fetch note (for GET and security check)
    note = conn.execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?",
        (note_id, session["user_id"])
    ).fetchone()

    if note is None:
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


@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form["email"]
        token = str(uuid.uuid4())

        conn = get_db_connection()

        # Step 1: Check if email exists (safe way)
        user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        # Step 2: Only update token if user exists
        if user:
            conn.execute(
                "UPDATE users SET reset_token = ? WHERE email = ?",
                (token, email)
            )
            conn.commit()

        conn.close()

        # Step 3: Always show same message (prevents email enumeration)
        reset_link = f"{MAIL_CONFIG['BASE_URL']}/reset/{token}"

        if user:
            msg = EmailMessage()
            msg["Subject"] = "Reset Password – Flask Notes"
            msg["From"] = MAIL_CONFIG["MAIL_USERNAME"]
            msg["To"] = email

            # Plain text
            msg.set_content(f"""
Hello,

You requested to reset your password for Flask Notes.

Reset your password using the link below:
{reset_link}

If you did not request this, please ignore this email.

Regards,
Flask Notes Team
""")

            # HTML email
            msg.add_alternative(f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2>Reset Your Password</h2>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_link}"
                   style="
                     background:#0d6efd;
                     color:white;
                     padding:12px 20px;
                     text-decoration:none;
                     border-radius:6px;
                     display:inline-block;
                   ">
                   Reset Password
                </a>
                <p>If you didn’t request this, ignore this email.</p>
              </body>
            </html>
            """, subtype="html")

            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(
                MAIL_CONFIG["MAIL_USERNAME"],
                MAIL_CONFIG["MAIL_PASSWORD"]
            )
            server.send_message(msg)
            server.quit()

        flash("If the email exists, a reset link has been sent.", "info")
        return redirect(url_for("login"))

    return render_template("forgot.html")



@app.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    conn = get_db_connection()

    # Check if token exists
    user = conn.execute(
        "SELECT id FROM users WHERE reset_token = ?",
        (token,)
    ).fetchone()

    if user is None:
        conn.close()
        flash("Invalid or expired reset link", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        password = generate_password_hash(request.form["password"])

        conn.execute(
            "UPDATE users SET password = ?, reset_token = NULL WHERE reset_token = ?",
            (password, token)
        )
        conn.commit()
        conn.close()

        flash("Password updated successfully", "success")
        return redirect(url_for("login"))

    conn.close()
    return render_template("reset.html")


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run()
