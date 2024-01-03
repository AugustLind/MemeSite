from flask import Blueprint, render_template, request, flash, jsonify, send_from_directory, current_app, redirect, url_for
from flask_login import login_required, current_user
from .models import Note
from . import db
import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note_to_delete = Note.query.get(noteId)
    if note_to_delete and note_to_delete.user_id == current_user.id:
        db.session.delete(note_to_delete)
        db.session.commit()

    return jsonify({})

@views.route('/profile', methods=['GET'])
def profile_page():
    return render_template("profile.html", user=current_user)

@views.route('/game', methods=['GET'])
def game():
    # Get the path to the image folder (assuming it's under the "static" folder)
    image_folder = os.path.join(current_app.root_path, 'static', 'images')

    # Get a list of image filenames from the folder
    image_files = os.listdir(image_folder)

    # Select three random images
    selected_images = random.sample(image_files, 3)

    return render_template("game.html", user=current_user, selected_images=selected_images)

@views.route('/create-meme', methods=['POST'])
@login_required
def create_meme():
    if request.method == 'POST':
        # Get the selected image and meme text from the form
        image_filename = request.form.get('image_filename')
        meme_text = request.form.get('memeText')

        # Process the image and add text
        image_path = os.path.join('/static/images', image_filename)
        meme_image = create_meme_image(image_path, meme_text)

        # Save the meme image or do further processing as needed
        meme_image.save('/static/save_memes.jpg')

        # You can add additional logic, such as saving the meme in the database, etc.

    return redirect(url_for('views.game'))


def create_meme_image(image_path, meme_text):
    # Load the original image
    original_image = Image.open(image_path)

    # Add text to the image
    draw = ImageDraw.Draw(original_image)
    font = ImageFont.load_default()  # You can customize the font and size
    draw.text((10, 10), meme_text, fill='white', font=font)

    return original_image

@views.route('/image/<filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'images'), filename)
