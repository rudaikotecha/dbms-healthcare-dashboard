from flask import render_template
from ..auth.routes import login_required
from ..db import get_db
from . import bp


@bp.get("/dashboard")
@login_required
def dashboard():
    db = get_db()
    stats = {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
             for table in ("patient", "doctor", "sample", "device")}
    latest = db.execute("SELECT sample_id, reaction_status, collection_time, f_name, l_name FROM sample JOIN patient ON patient.patient_id=sample.p_id ORDER BY sample_id DESC LIMIT 5").fetchall()
    return render_template("main/dashboard.html", stats=stats, latest=latest)
