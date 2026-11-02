from datetime import date
import os

from flask import Flask, abort, g, redirect, render_template, request, url_for

import auth
import db
import profile
from auth import login_required


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "jobtrack.sqlite"),
        UPLOAD_FOLDER=os.path.join(app.instance_path, "cvs"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )
    app.config.from_pyfile("config.py", silent=True)
    
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(profile.bp)

    @app.route("/")
    @login_required
    def index():
        conn = db.get_db()

        status = request.args.get("status")
        if status in ("Applied", "Interview", "Offer", "Rejected"):
            applications = conn.execute(
                "SELECT * FROM applications WHERE user_id = ? AND status = ?"
                " ORDER BY date_applied DESC",
                (g.user["id"], status),
            ).fetchall()
        else:
            status = None
            applications = conn.execute(
                "SELECT * FROM applications WHERE user_id = ?"
                " ORDER BY date_applied DESC",
                (g.user["id"],),
            ).fetchall()

        counts = {}
        for row in conn.execute(
            "SELECT status, COUNT(*) AS n FROM applications"
            " WHERE user_id = ? GROUP BY status",
            (g.user["id"],),
        ).fetchall():
            counts[row["status"]] = row["n"]

        return render_template(
            "index.html",
            applications=applications,
            counts=counts,
            total=sum(counts.values()),
            current_status=status,
            today=date.today().isoformat(),
        )

    @app.route("/add", methods=("GET", "POST"))
    @login_required
    def add():
        if request.method == "POST":
            conn = db.get_db()
            conn.execute(
                "INSERT INTO applications"
                " (user_id, company, role, link, status, date_applied,"
                " follow_up_date, notes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    g.user["id"],
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

    @app.route("/<int:id>/edit", methods=("GET", "POST"))
    @login_required
    def edit(id):
        conn = db.get_db()
        application = conn.execute(
            "SELECT * FROM applications WHERE id = ? AND user_id = ?",
            (id, g.user["id"]),
        ).fetchone()

        if application is None:
            abort(404)

        if request.method == "POST":
            conn.execute(
                "UPDATE applications SET company = ?, role = ?, link = ?,"
                " status = ?, date_applied = ?, follow_up_date = ?, notes = ?"
                " WHERE id = ? AND user_id = ?",
                (
                    request.form["company"],
                    request.form["role"],
                    request.form["link"],
                    request.form["status"],
                    request.form["date_applied"],
                    request.form["follow_up_date"] or None,
                    request.form["notes"],
                    id,
                    g.user["id"],
                ),
            )
            conn.commit()
            return redirect(url_for("index"))

        return render_template("edit.html", application=application)

    @app.route("/<int:id>/delete", methods=("POST",))
    @login_required
    def delete(id):
        conn = db.get_db()
        application = conn.execute(
            "SELECT * FROM applications WHERE id = ? AND user_id = ?",
            (id, g.user["id"]),
        ).fetchone()

        if application is None:
            abort(404)

        conn.execute(
            "DELETE FROM applications WHERE id = ? AND user_id = ?",
            (id, g.user["id"]),
        )
        conn.commit()
        return redirect(url_for("index"))

    return app