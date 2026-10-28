import os

from flask import Flask, abort, redirect, render_template, request, url_for

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

        status = request.args.get("status")
        if status in ("Applied", "Interview", "Offer", "Rejected"):
            applications = conn.execute(
                "SELECT * FROM applications WHERE status = ?"
                " ORDER BY date_applied DESC",
                (status,),
            ).fetchall()
        else:
            status = None
            applications = conn.execute(
                "SELECT * FROM applications ORDER BY date_applied DESC"
            ).fetchall()

        counts = {}
        for row in conn.execute(
            "SELECT status, COUNT(*) AS n FROM applications GROUP BY status"
        ).fetchall():
            counts[row["status"]] = row["n"]

        return render_template(
            "index.html",
            applications=applications,
            counts=counts,
            total=sum(counts.values()),
            current_status=status,
        )

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

    @app.route("/<int:id>/edit", methods=("GET", "POST"))
    def edit(id):
        conn = db.get_db()
        application = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (id,)
        ).fetchone()

        if application is None:
            abort(404)

        if request.method == "POST":
            conn.execute(
                "UPDATE applications SET company = ?, role = ?, link = ?,"
                " status = ?, date_applied = ?, follow_up_date = ?, notes = ?"
                " WHERE id = ?",
                (
                    request.form["company"],
                    request.form["role"],
                    request.form["link"],
                    request.form["status"],
                    request.form["date_applied"],
                    request.form["follow_up_date"] or None,
                    request.form["notes"],
                    id,
                ),
            )
            conn.commit()
            return redirect(url_for("index"))

        return render_template("edit.html", application=application)

    @app.route("/<int:id>/delete", methods=("POST",))
    def delete(id):
        conn = db.get_db()
        application = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (id,)
        ).fetchone()

        if application is None:
            abort(404)

        conn.execute("DELETE FROM applications WHERE id = ?", (id,))
        conn.commit()
        return redirect(url_for("index"))

    return app