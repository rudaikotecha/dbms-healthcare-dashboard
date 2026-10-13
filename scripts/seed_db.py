"""Create one local doctor account and fictional sample records.

Usage:
    flask --app run.py seed-db --username demo --password choose-a-password
"""
import sqlite3

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from app.db import get_db


@click.command("seed-db")
@click.option("--username", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def seed_db_command(username, password):
    """Create a doctor login and a small fictional dataset for a demo."""
    if len(password) < 8:
        raise click.ClickException("Choose a password with at least 8 characters.")

    db = get_db()
    try:
        with db:
            db.execute(
                "INSERT INTO account (username, password_hash, login_type) "
                "VALUES (?, ?, 'Doctor')",
                (username, generate_password_hash(password)),
            )

            if db.execute("SELECT 1 FROM patient LIMIT 1").fetchone() is None:
                patient_id = db.execute(
                    "INSERT INTO patient (f_name, l_name, gender, dob) "
                    "VALUES (?, ?, ?, ?)",
                    ("Alex", "Rivera", "Other", "1990-04-12"),
                ).lastrowid
                db.execute(
                    "INSERT INTO p_contact (patient_id, contact) VALUES (?, ?)",
                    (patient_id, "alex@example.test"),
                )
                doctor_id = db.execute(
                    "INSERT INTO doctor (name, department, p_id) VALUES (?, ?, ?)",
                    ("Morgan Lee", "Diagnostics", patient_id),
                ).lastrowid
                db.execute(
                    "INSERT INTO clinician (doctor_id, designation) VALUES (?, ?)",
                    (doctor_id, "Clinician"),
                )
                sample_id = db.execute(
                    "INSERT INTO sample (reaction_status, collection_time, p_id) "
                    "VALUES (?, ?, ?)",
                    ("Pending", "2026-10-10T09:30", patient_id),
                ).lastrowid
                db.execute(
                    "INSERT INTO device (calibration_date, s_id) VALUES (?, ?)",
                    ("2026-10-01", sample_id),
                )
                db.execute(
                    "INSERT INTO urine_strip (manufacturer_name, s_id) VALUES (?, ?)",
                    ("Fictional Diagnostics", sample_id),
                )
    except sqlite3.IntegrityError as error:
        raise click.ClickException(
            "Could not create the account. That username may already be in use."
        ) from error

    click.echo(f"Created the doctor account '{username}'.")


def register(app):
    app.cli.add_command(seed_db_command)
