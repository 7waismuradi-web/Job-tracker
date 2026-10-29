import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

import db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = db.get_db().execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view

@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        name = request.form["name"].strip()
        course = request.form["course"].strip() or None
        year = request.form["year_of_study"] or None
        conn = db.get_db()
        error = None

        if not name:
            error = "Name is required."
        elif not email:
            error = "Email is required."
        elif "@" not in email:
            error = "Please enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."

        if error is None:
            try:
                conn.execute(
                    "INSERT INTO users"
                    " (email, password_hash, name, course, year_of_study)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (
                        email,
                        generate_password_hash(password),
                        name,
                        course,
                        year,
                    ),
                )
                conn.commit()
            except db.sqlite3.IntegrityError:
                error = "An account with that email already exists."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")

@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = db.get_db()
        error = None

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if user is None or not check_password_hash(
            user["password_hash"], password
        ):
            error = "Incorrect email or password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))