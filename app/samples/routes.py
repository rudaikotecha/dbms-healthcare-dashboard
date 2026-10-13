import sqlite3
from datetime import datetime
from flask import flash, redirect, render_template, request, url_for
from ..auth.routes import login_required
from ..db import get_db
from . import bp


@bp.get("/")
@login_required
def index():
    rows=get_db().execute("SELECT s.*,p.f_name,p.l_name FROM sample s JOIN patient p ON p.patient_id=s.p_id ORDER BY s.sample_id DESC").fetchall()
    return render_template("samples/list.html",samples=rows)


@bp.route("/new",methods=["GET","POST"])
@login_required
def create():
    db=get_db(); patients=db.execute("SELECT patient_id,f_name,l_name FROM patient ORDER BY l_name").fetchall()
    if request.method=="POST":
        status=request.form.get("reaction_status","").strip(); collected=request.form.get("collection_time","").strip(); pid=request.form.get("p_id","")
        try: datetime.fromisoformat(collected)
        except ValueError: collected=""
        if not status or not collected or not pid.isdigit(): flash("Provide a status, valid collection time, and patient.","error")
        else:
            try:
                with db: cur=db.execute("INSERT INTO sample(reaction_status,collection_time,p_id) VALUES(?,?,?)",(status,collected,int(pid)))
                flash("Sample registered.","success"); return redirect(url_for("samples.detail",sample_id=cur.lastrowid))
            except sqlite3.IntegrityError: flash("Select an existing patient.","error")
    return render_template("samples/form.html",patients=patients,sample=None)


@bp.get("/<int:sample_id>")
@login_required
def detail(sample_id):
    db=get_db(); sample=db.execute("SELECT s.*,p.f_name,p.l_name FROM sample s JOIN patient p ON p.patient_id=s.p_id WHERE s.sample_id=?",(sample_id,)).fetchone()
    if not sample:
        from flask import abort; abort(404)
    devices=db.execute("SELECT * FROM device WHERE s_id=?",(sample_id,)).fetchall()
    strips=db.execute("SELECT * FROM urine_strip WHERE s_id=?",(sample_id,)).fetchall()
    pads=db.execute("SELECT r.*,d.calibration_date FROM reagent_pad r JOIN device d ON d.device_id=r.d_id WHERE r.s_id=?",(sample_id,)).fetchall()
    return render_template("samples/detail.html",sample=sample,devices=devices,strips=strips,pads=pads)


@bp.route("/<int:sample_id>/edit",methods=["GET","POST"])
@login_required
def edit(sample_id):
    db=get_db(); sample=db.execute("SELECT * FROM sample WHERE sample_id=?",(sample_id,)).fetchone()
    if not sample:
        from flask import abort; abort(404)
    patients=db.execute("SELECT patient_id,f_name,l_name FROM patient ORDER BY l_name").fetchall()
    if request.method=="POST":
        status=request.form.get("reaction_status","").strip(); collected=request.form.get("collection_time","").strip(); pid=request.form.get("p_id","")
        try: datetime.fromisoformat(collected)
        except ValueError: collected=""
        if not(status and collected and pid.isdigit()): flash("Provide a status, valid collection time, and patient.","error")
        else:
            try:
                with db: db.execute("UPDATE sample SET reaction_status=?,collection_time=?,p_id=? WHERE sample_id=?",(status,collected,int(pid),sample_id))
                flash("Sample updated.","success"); return redirect(url_for("samples.detail",sample_id=sample_id))
            except sqlite3.IntegrityError: flash("Select an existing patient.","error")
    return render_template("samples/form.html",patients=patients,sample=sample)


@bp.post("/<int:sample_id>/delete")
@login_required
def delete(sample_id):
    db=get_db()
    try:
        with db: db.execute("DELETE FROM sample WHERE sample_id=?",(sample_id,))
        flash("Sample deleted.","success")
    except sqlite3.IntegrityError: flash("Sample has related device or strip records and cannot be deleted.","error")
    return redirect(url_for("samples.index"))


@bp.route("/<int:sample_id>/related",methods=["POST"])
@login_required
def related(sample_id):
    db=get_db()
    if not db.execute("SELECT 1 FROM sample WHERE sample_id=?",(sample_id,)).fetchone():
        from flask import abort; abort(404)
    kind=request.form.get("kind")
    try:
        with db:
            if kind=="device":
                db.execute("INSERT INTO device(calibration_date,s_id) VALUES(?,?)",(request.form.get("calibration_date",""),sample_id))
            elif kind=="strip":
                db.execute("INSERT INTO urine_strip(manufacturer_name,s_id) VALUES(?,?)",(request.form.get("manufacturer_name","").strip(),sample_id))
            elif kind=="pad":
                device_id=request.form.get("device_id","")
                db.execute("INSERT INTO reagent_pad(pad_position,s_id,d_id,red_value,green_value,blue_value,analyte) VALUES(?,?,?,?,?,?,?)",(int(request.form["pad_position"]),sample_id,int(device_id),int(request.form["red_value"]),int(request.form["green_value"]),int(request.form["blue_value"]),request.form["analyte"].strip()))
            else: raise ValueError
        flash("Related record added.","success")
    except (ValueError,KeyError,sqlite3.IntegrityError): flash("Related record was not saved. Check the values and selected device.","error")
    return redirect(url_for("samples.detail",sample_id=sample_id))
