"""Application factory and database configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__)
    load_dotenv(Path(app.root_path).parent / ".env", override=False)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///database.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config is not None:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError(
            "Set SECRET_KEY in your environment or local .env file before starting MemeSite."
        )

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .models import User, Note  # noqa: F401: register models before create_all

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    return app
