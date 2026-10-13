import sqlite3

import pytest
from app import create_app
from werkzeug.security import generate_password_hash


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DATABASE": str(tmp_path / "test.sqlite3"),
    })

    with app.app_context():
        from app.db import get_db, init_db

        init_db()
        get_db().execute(
            "INSERT INTO account (username, password_hash, login_type) VALUES (?, ?, ?)",
            ("tester", generate_password_hash("test-password"), "Doctor"),
        )
        get_db().commit()

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_token(client):
    client.get("/auth/login")
    with client.session_transaction() as session:
        return session["csrf_token"]


def login(client):
    return client.post(
        "/auth/login",
        data={
            "csrf_token": csrf_token(client),
            "username": "tester",
            "password": "test-password",
        },
        follow_redirects=True,
    )
