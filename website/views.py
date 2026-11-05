from io import BytesIO
from pathlib import Path
import random

from flask import (
    Blueprint, abort, current_app, flash, jsonify, render_template,
    request, send_file, send_from_directory,
)
from flask_login import current_user, login_required
from PIL import Image, ImageDraw, ImageFont

from . import db
from .models import Note

views = Blueprint("views", __name__)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def image_directory():
    return Path(current_app.config.get("MEME_IMAGE_DIR") or
                Path(current_app.root_path) / "static" / "images").resolve()


@views.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        note = request.form.get("note", "")
        if not 1 <= len(note) <= 10000:
            flash("Note must contain between 1 and 10000 characters.", category="error")
        else:
            db.session.add(Note(data=note, user_id=current_user.id))
            db.session.commit()
            flash("Note added!", category="success")
    return render_template("home.html", user=current_user)


@views.route("/delete-note", methods=["POST"])
@login_required
def delete_note():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or type(payload.get("noteId")) is not int:
        abort(400)
    note = db.session.get(Note, payload["noteId"])
    if note is None or note.user_id != current_user.id:
        abort(404)
    db.session.delete(note)
    db.session.commit()
    return jsonify({})


@views.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html", user=current_user)


@views.route("/game")
@login_required
def game():
    directory = image_directory()
    files = sorted(
        path.name for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ) if directory.is_dir() else []
    selected = random.sample(files, min(3, len(files)))
    return render_template("game.html", user=current_user, selected_images=selected)


@views.route("/create-meme", methods=["POST"])
@login_required
def create_meme():
    filename = request.form.get("image_filename", "")
    text = request.form.get("memeText", "").strip()
    if not filename or not 1 <= len(text) <= 1000:
        abort(400)

    directory = image_directory()
    image_path = (directory / filename).resolve()
    if (Path(filename).name != filename or image_path.parent != directory
            or image_path.suffix.lower() not in IMAGE_EXTENSIONS
            or not image_path.is_file()):
        abort(404)

    try:
        meme = create_meme_image(image_path, text)
    except OSError:
        abort(400, description="The selected image could not be opened.")
    output = BytesIO()
    meme.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype="image/png", as_attachment=True,
                     download_name="meme.png")


def create_meme_image(image_path, meme_text):
    with Image.open(image_path) as original:
        image = original.convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), meme_text, fill="white", font=ImageFont.load_default())
    return image


@views.route("/image/<filename>")
def serve_image(filename):
    return send_from_directory(image_directory(), filename)
