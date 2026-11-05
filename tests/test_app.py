"""Regression checks using a fresh in-memory database and synthetic images."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from website import create_app, db
from website.models import Note, User


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.images = Path(self.temp.name) / 'images'
        self.images.mkdir()
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-only-session-signing-value',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'MEME_IMAGE_DIR': str(self.images),
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            owner = User(email='owner@example.test', first_name='Owner', password='unused')
            other = User(email='other@example.test', first_name='Other', password='unused')
            db.session.add_all([owner, other])
            db.session.commit()
            self.owner_id, self.other_id = owner.id, other.id
        self.addCleanup(self.dispose_database)

    def dispose_database(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def log_in(self):
        with self.client.session_transaction() as session:
            session['_user_id'] = str(self.owner_id)
            session['_fresh'] = True

    def test_missing_secret_fails_clearly(self):
        with patch.dict(os.environ, {}, clear=True), patch('website.load_dotenv'):
            with self.assertRaisesRegex(RuntimeError, 'SECRET_KEY'):
                create_app()

    def test_anonymous_private_routes_redirect(self):
        for path in ['/', '/profile', '/game']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 302)
        self.assertEqual(self.client.post('/delete-note', json={'noteId': 1}).status_code, 302)
        self.assertEqual(self.client.post('/create-meme').status_code, 302)

    def test_empty_game_and_small_image_library(self):
        self.log_in()
        self.assertIn(b'No meme images', self.client.get('/game').data)
        Image.new('RGB', (80, 80), 'black').save(self.images / 'sample.png')
        response = self.client.get('/game')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'imageModal1', response.data)
        self.assertIn(b'name="image_filename" value="sample.png"', response.data)

    def test_meme_download_keeps_original(self):
        self.log_in()
        source = self.images / 'sample.png'
        Image.new('RGB', (80, 80), 'black').save(source)
        before = source.read_bytes()
        response = self.client.post('/create-meme', data={
            'image_filename': 'sample.png', 'memeText': 'Hello',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')
        self.assertIn('attachment', response.headers['Content-Disposition'])
        self.assertTrue(response.data.startswith(b'\x89PNG'))
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(list(self.images.iterdir()), [source])

    def test_image_paths_and_text_are_validated(self):
        self.log_in()
        Image.new('RGB', (80, 80)).save(Path(self.temp.name) / 'outside.png')
        for filename in ['../outside.png', str(Path(self.temp.name) / 'outside.png'), 'missing.png']:
            with self.subTest(filename=filename):
                response = self.client.post('/create-meme', data={
                    'image_filename': filename, 'memeText': 'Hello',
                })
                self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.post('/create-meme').status_code, 400)
        self.assertEqual(self.client.post('/create-meme', data={
            'image_filename': 'sample.png', 'memeText': 'x' * 1001,
        }).status_code, 400)

    def test_note_deletion_requires_ownership(self):
        self.log_in()
        with self.app.app_context():
            note = Note(data='Other user note', user_id=self.other_id)
            db.session.add(note)
            db.session.commit()
            note_id = note.id
        self.assertEqual(self.client.post('/delete-note', json={'noteId': note_id}).status_code, 404)
        self.assertEqual(self.client.post('/delete-note', json=[]).status_code, 400)
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Note, note_id))

    def test_empty_auth_forms_do_not_crash(self):
        self.assertEqual(self.client.post('/sign-up', data={}).status_code, 200)
        self.assertEqual(self.client.post('/login', data={}).status_code, 200)

    def test_signup_logout_and_login(self):
        response = self.client.post('/sign-up', data={
            'email': 'new@example.test', 'firstName': 'New',
            'password1': 'test-password-123', 'password2': 'test-password-123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get('/profile').status_code, 200)
        self.client.get('/logout')
        response = self.client.post('/login', data={
            'email': 'new@example.test', 'password': 'test-password-123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get('/profile').status_code, 200)


if __name__ == '__main__':
    unittest.main()
