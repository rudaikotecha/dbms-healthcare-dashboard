import sqlite3
from flask import flash, redirect, render_template, request, url_for
from ..auth.routes import login_required
from ..db import get_db
from . import bp


@bp.get("/")
@login_required
def index():
    rows = get_db().execute("SELECT d.*,p.f_name,p.l_name,c.designation clinician_designation,k.designation consultant_designation FROM doctor d JOIN patient p ON p.patient_id=d.p_id LEFT JOIN clinician c ON c.doctor_id=d.doctor_id LEFT JOIN consultant k ON k.doctor_id=d.doctor_id ORDER BY d.name").fetchall()
    return render_template("doctors/list.html", doctors=rows)


@bp.get("/<int:doctor_id>")
@login_required
def detail(doctor_id):
    row = get_db().execute("SELECT d.*,p.f_name,p.l_name,c.designation clinician_designation,k.designation consultant_designation FROM doctor d JOIN patient p ON p.patient_id=d.p_id LEFT JOIN clinician c ON c.doctor_id=d.doctor_id LEFT JOIN consultant k ON k.doctor_id=d.doctor_id WHERE d.doctor_id=?", (doctor_id,)).fetchone()
    if row is None:
        from flask import abort
        abort(404)
    return render_template("doctors/detail.html", doctor=row)

def form_data():
    return tuple(request.form.get(k, "").strip() for k in ("name", "department", "p_id", "kind", "designation"))


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    db=get_db(); patients=db.execute("SELECT patient_id,f_name,l_name FROM patient ORDER BY l_name").fetchall()
    if request.method == "POST":
        name, department, p_id, kind, designation = form_data()
        if not (name and department and p_id.isdigit() and kind in ("Clinician", "Consultant") and designation):
            flash("Complete all doctor fields.", "error")
        else:
            try:
                with db:
                    cur=db.execute("INSERT INTO doctor(name,department,p_id) VALUES(?,?,?)", (name,department,int(p_id)))
                    table="clinician" if kind=="Clinician" else "consultant"
                    db.execute(f"INSERT INTO {table}(doctor_id,designation) VALUES(?,?)", (cur.lastrowid,designation))
                flash("Doctor added.", "success"); return redirect(url_for("doctors.index"))
            except sqlite3.IntegrityError:
                flash("Select an existing patient and provide valid doctor details.", "error")
    return render_template("doctors/form.html", patients=patients, doctor=None)


@bp.route("/<int:doctor_id>/edit", methods=["GET", "POST"])
@login_required
def edit(doctor_id):
    db=get_db(); doctor=db.execute("SELECT d.*,coalesce(c.designation,k.designation) designation,CASE WHEN c.doctor_id IS NOT NULL THEN 'Clinician' ELSE 'Consultant' END kind FROM doctor d LEFT JOIN clinician c USING(doctor_id) LEFT JOIN consultant k USING(doctor_id) WHERE d.doctor_id=?",(doctor_id,)).fetchone()
    if not doctor:
        from flask import abort; abort(404)
    patients=db.execute("SELECT patient_id,f_name,l_name FROM patient ORDER BY l_name").fetchall()
    if request.method=="POST":
        name,department,p_id,kind,designation=form_data()
        if not (name and department and p_id.isdigit() and kind in ("Clinician","Consultant") and designation): flash("Complete all doctor fields.","error")
        else:
            try:
                with db:
                    db.execute("UPDATE doctor SET name=?,department=?,p_id=? WHERE doctor_id=?",(name,department,int(p_id),doctor_id))
                    db.execute("DELETE FROM clinician WHERE doctor_id=?",(doctor_id,)); db.execute("DELETE FROM consultant WHERE doctor_id=?",(doctor_id,))
                    table="clinician" if kind=="Clinician" else "consultant"
                    db.execute(f"INSERT INTO {table}(doctor_id,designation) VALUES(?,?)",(doctor_id,designation))
                flash("Doctor updated.","success"); return redirect(url_for("doctors.index"))
            except sqlite3.IntegrityError: flash("Select an existing patient and provide valid details.","error")
    return render_template("doctors/form.html",patients=patients,doctor=doctor)


@bp.post("/<int:doctor_id>/delete")
@login_required
def delete(doctor_id):
    db=get_db()
    try:
        with db: db.execute("DELETE FROM doctor WHERE doctor_id=?",(doctor_id,))
        flash("Doctor deleted.","success")
    except sqlite3.IntegrityError: flash("Doctor could not be deleted because it has related records.","error")
    return redirect(url_for("doctors.index"))
