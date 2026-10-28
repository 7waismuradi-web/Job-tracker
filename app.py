import os

from flask import Flask, redirect, render_template, request, url_for

import db


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "jobtrack.sqlite"),
    )

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    @app.route("/")
    def index():
        conn = db.get_db()
        applications = conn.execute(
            "SELECT * FROM applications ORDER BY date_applied DESC"
        ).fetchall()
        return render_template("index.html", applications=applications)

    @app.route("/add", methods=("GET", "POST"))
    def add():
        if request.method == "POST":
            conn = db.get_db()
            conn.execute(
                "INSERT INTO applications"
                " (user_id, company, role, link, status, date_applied,"
                " follow_up_date, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    1,
                    request.form["company"],
                    request.form["role"],
                    request.form["link"],
                    request.form["status"],
                    request.form["date_applied"],
                    request.form["follow_up_date"] or None,
                    request.form["notes"],
                ),
            )
            conn.commit()
            return redirect(url_for("index"))

        return render_template("add.html")

    return app