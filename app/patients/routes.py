import sqlite3
from datetime import date
from flask import flash, redirect, render_template, request, url_for
from ..auth.routes import login_required
from ..db import get_db
from . import bp


def values():
    return (request.form.get("f_name", "").strip(), request.form.get("l_name", "").strip(),
            request.form.get("gender", ""), request.form.get("dob", ""))


def valid(data):
    first, last, gender, dob = data
    try:
        parsed = date.fromisoformat(dob)
    except ValueError:
        return False
    return bool(first and last and gender in {"Female", "Male", "Other", "Prefer not to say"} and parsed <= date.today())


@bp.get("/")
@login_required
def index():
    patients = get_db().execute("SELECT p.*, (SELECT COUNT(*) FROM sample s WHERE s.p_id=p.patient_id) sample_count FROM patient p ORDER BY l_name, f_name").fetchall()
    return render_template("patients/list.html", patients=patients)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        data = values()
        contacts = [x.strip() for x in request.form.get("contacts", "").splitlines() if x.strip()]
        if not valid(data):
            flash("Enter names, a valid gender, and a valid date of birth (not in the future).", "error")
        else:
            db = get_db()
            try:
                with db:
                    cur = db.execute("INSERT INTO patient(f_name,l_name,gender,dob) VALUES(?,?,?,?)", data)
                    db.executemany("INSERT INTO p_contact(patient_id,contact) VALUES(?,?)", [(cur.lastrowid, c) for c in contacts])
                flash("Patient added.", "success")
                return redirect(url_for("patients.detail", patient_id=cur.lastrowid))
            except sqlite3.IntegrityError:
                flash("The patient could not be saved because a database constraint was not met.", "error")
    return render_template("patients/form.html", patient=None, contacts="")


@bp.get("/<int:patient_id>")
@login_required
def detail(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if patient is None:
        from flask import abort; abort(404)
    contacts = db.execute("SELECT contact FROM p_contact WHERE patient_id=?", (patient_id,)).fetchall()
    samples = db.execute("SELECT * FROM sample WHERE p_id=? ORDER BY sample_id DESC", (patient_id,)).fetchall()
    doctors = db.execute("SELECT * FROM doctor WHERE p_id=? ORDER BY name", (patient_id,)).fetchall()
    return render_template("patients/detail.html", patient=patient, contacts=contacts, samples=samples, doctors=doctors)


@bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
def edit(patient_id):
    db = get_db(); patient = db.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if patient is None:
        from flask import abort; abort(404)
    existing = db.execute("SELECT contact FROM p_contact WHERE patient_id=?", (patient_id,)).fetchall()
    if request.method == "POST":
        data = values(); contacts = [x.strip() for x in request.form.get("contacts", "").splitlines() if x.strip()]
        if not valid(data):
            flash("Enter valid patient details and a date of birth that is not in the future.", "error")
        else:
            try:
                with db:
                    db.execute("UPDATE patient SET f_name=?,l_name=?,gender=?,dob=? WHERE patient_id=?", (*data, patient_id))
                    db.execute("DELETE FROM p_contact WHERE patient_id=?", (patient_id,))
                    db.executemany("INSERT INTO p_contact(patient_id,contact) VALUES(?,?)", [(patient_id, c) for c in contacts])
                flash("Patient updated.", "success")
                return redirect(url_for("patients.detail", patient_id=patient_id))
            except sqlite3.IntegrityError:
                flash("Patient details could not be saved.", "error")
    return render_template("patients/form.html", patient=patient, contacts="\n".join(r["contact"] for r in existing))


@bp.post("/<int:patient_id>/delete")
@login_required
def delete(patient_id):
    db = get_db()
    try:
        with db: db.execute("DELETE FROM patient WHERE patient_id=?", (patient_id,))
        flash("Patient deleted.", "success")
    except sqlite3.IntegrityError:
        flash("This patient has related records and cannot be deleted.", "error")
    return redirect(url_for("patients.index"))
