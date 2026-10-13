import hmac
import os
import secrets
from datetime import date
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for

from .config import Config
from .db import init_app as init_db_app


def create_app(test_config=None):
    """Build and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    if not app.config.get("DATABASE"):
        app.config["DATABASE"] = os.path.join(app.instance_path, "healthcare.sqlite3")

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db_app(app)

    from scripts.seed_db import register as register_seed_command
    register_seed_command(app)

    @app.context_processor
    def template_helpers():
        def csrf_token():
            token = session.get("csrf_token")
            if token is None:
                token = secrets.token_urlsafe(32)
                session["csrf_token"] = token
            return token

        return {"csrf_token": csrf_token, "today": date.today().isoformat()}

    @app.before_request
    def protect_forms():
        if not app.config.get("WTF_CSRF_ENABLED", True):
            return
        if request.method != "POST":
            return

        submitted_token = request.form.get("csrf_token", "")
        session_token = session.get("csrf_token", "")
        if not submitted_token or not session_token:
            abort(400, "Invalid or missing form security token.")
        if not hmac.compare_digest(submitted_token, session_token):
            abort(400, "Invalid or missing form security token.")

    from .auth import bp as auth_bp
    from .doctors import bp as doctors_bp
    from .main import bp as main_bp
    from .patients import bp as patients_bp
    from .samples import bp as samples_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(samples_bp)

    @app.get("/")
    def index():
        return redirect(url_for("main.dashboard"))

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    return app
