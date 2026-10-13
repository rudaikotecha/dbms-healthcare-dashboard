from .conftest import csrf_token, login


def test_app_creation_and_protected_redirect(client):
    assert client.get("/auth/login").status_code == 200

    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_doctor_registration_and_login(client):
    token = csrf_token(client)
    response = client.post(
        "/auth/register",
        data={
            "csrf_token": token,
            "username": "new_doctor",
            "password": "safe-password-123",
            "confirm_password": "safe-password-123",
        },
        follow_redirects=True,
    )
    assert b"Doctor account created" in response.data

    token = csrf_token(client)
    response = client.post(
        "/auth/login",
        data={
            "csrf_token": token,
            "username": "new_doctor",
            "password": "safe-password-123",
        },
        follow_redirects=True,
    )
    assert b"Healthcare Management" in response.data


def test_login_rejects_wrong_password(client):
    response = client.post(
        "/auth/login",
        data={
            "csrf_token": csrf_token(client),
            "username": "tester",
            "password": "wrong-password",
        },
        follow_redirects=True,
    )
    assert b"incorrect" in response.data


def test_patient_create_validate_list_and_logout(client):
    login(client)
    token = csrf_token(client)

    invalid = client.post(
        "/patients/new",
        data={
            "csrf_token": token,
            "f_name": "",
            "l_name": "Test",
            "gender": "Male",
            "dob": "1990-01-01",
        },
        follow_redirects=True,
    )
    assert b"valid gender" in invalid.data

    created = client.post(
        "/patients/new",
        data={
            "csrf_token": token,
            "f_name": "Sam",
            "l_name": "Example",
            "gender": "Other",
            "dob": "1990-01-01",
            "contacts": "sam@example.test\n555-0100",
        },
        follow_redirects=True,
    )
    assert b"Patient added" in created.data
    assert b"Sam Example" in client.get("/patients/").data

    logged_out = client.post(
        "/auth/logout", data={"csrf_token": token}, follow_redirects=True
    )
    assert b"signed out" in logged_out.data


def test_foreign_key_constraint(app):
    with app.app_context():
        from app.db import get_db

        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                "INSERT INTO sample (reaction_status, collection_time, p_id) "
                "VALUES (?, ?, ?)",
                ("Pending", "2026-01-01T10:00", 999),
            )
