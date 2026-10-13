import sqlite3
from functools import wraps

from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_db
from . import bp


def login_required(view):
    """Send visitors to sign-in before showing a protected page."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "account_id" not in session:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Sign in with a doctor account."""
    if "account_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        account = get_db().execute(
            "SELECT account_id, username, password_hash "
            "FROM account WHERE username = ? AND login_type = 'Doctor'",
            (username,),
        ).fetchone()

        if account and check_password_hash(account["password_hash"], password):
            session.clear()
            session["account_id"] = account["account_id"]
            session["username"] = account["username"]

            next_page = request.args.get("next", "")
            if next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for("main.dashboard"))

        flash("Username or password is incorrect.", "error")

    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Create a doctor login using a one-way password hash."""
    if "account_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3 or len(username) > 40:
            flash("Choose a username between 3 and 40 characters.", "error")
        elif not username.replace("_", "").replace("-", "").replace(".", "").isalnum():
            flash("Username may contain letters, numbers, dots, hyphens, and underscores.", "error")
        elif len(password) < 8:
            flash("Choose a password with at least 8 characters.", "error")
        elif password != confirm_password:
            flash("The passwords do not match.", "error")
        else:
            db = get_db()
            try:
                with db:
                    db.execute(
                        "INSERT INTO account (username, password_hash, login_type) "
                        "VALUES (?, ?, 'Doctor')",
                        (username, generate_password_hash(password)),
                    )
                flash("Doctor account created. You can now sign in.", "success")
                return redirect(url_for("auth.login"))
            except sqlite3.IntegrityError:
                flash("That username is already registered. Choose another one.", "error")

    return render_template("auth/register.html")


@bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
