import os
import uuid

from flask import (
    Blueprint, abort, current_app, flash, g, redirect, render_template,
    request, send_file, url_for
)
from werkzeug.utils import secure_filename

import db
from auth import login_required

bp = Blueprint("profile", __name__, url_prefix="/profile")

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def extension_of(filename):
    return os.path.splitext(filename)[1].lower()


@bp.route("/", methods=("GET", "POST"))
@login_required
def index():
    conn = db.get_db()

    if request.method == "POST":
        conn.execute(
            "UPDATE users SET name = ?, course = ?, year_of_study = ?,"
            " phone = ?, address = ? WHERE id = ?",
            (
                request.form["name"].strip(),
                request.form["course"].strip() or None,
                request.form["year_of_study"] or None,
                request.form["phone"].strip() or None,
                request.form["address"].strip() or None,
                g.user["id"],
            ),
        )
        conn.commit()
        flash("Profile updated.")
        return redirect(url_for("profile.index"))

    return render_template("profile/index.html")


@bp.route("/cv", methods=("POST",))
@login_required
def upload_cv():
    file = request.files.get("cv")

    if file is None or file.filename == "":
        flash("Choose a file first.")
        return redirect(url_for("profile.index"))

    extension = extension_of(secure_filename(file.filename))

    if extension not in ALLOWED_EXTENSIONS:
        flash("Only PDF and Word documents are accepted.")
        return redirect(url_for("profile.index"))

    stored_name = f"{uuid.uuid4().hex}{extension}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name))

    conn = db.get_db()
    old = g.user["cv_filename"]

    conn.execute(
        "UPDATE users SET cv_filename = ? WHERE id = ?",
        (stored_name, g.user["id"]),
    )
    conn.commit()

    if old:
        try:
            os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], old))
        except OSError:
            pass

    flash("CV uploaded.")
    return redirect(url_for("profile.index"))


@bp.route("/cv/download")
@login_required
def download_cv():
    if not g.user["cv_filename"]:
        abort(404)


       