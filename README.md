# CareDesk Healthcare Management Dashboard

An educational Flask and SQLite project for a DBMS laboratory. It demonstrates HTML form submission, server-side validation, parameterized SQL, relational constraints, and querying records into Jinja templates. It is a prototype for fictional records and is not intended for real patient data.

## Stage 1 — relational model interpretation

No model image was attached to the conversation, so the supplied relation list is the schema source for this implementation. Please compare these assumptions with your diagram if you add it later.

| Relation | Primary key | Foreign key(s) |
|---|---|---|
| PATIENT | Patient_id | — |
| P_CONTACT | (Patient_id, Contact) | Patient_id → PATIENT |
| SAMPLE | Sample_id | P_id → PATIENT |
| DEVICE | Device_id | S_id → SAMPLE |
| URINE_STRIP | Manufacturer_id | S_id → SAMPLE |
| REAGENT_PAD | (Pad_position, S_id, D_id) | S_id → SAMPLE; D_id → DEVICE |
| DOCTOR | Doctor_id | P_id → PATIENT |
| CLINICIAN | Doctor_id | Doctor_id → DOCTOR |
| CONSULTANT | Doctor_id | Doctor_id → DOCTOR |

Assumptions: `P_CONTACT` is multivalued, hence its composite key. `CLINICIAN` and `CONSULTANT` are one-to-one subtype tables, each keyed by the doctor id. `DOCTOR.P_id` is treated as a required patient association because that is the relationship listed; this is unusual for a general doctor directory, so confirm the diagram. `SAMPLE.P_id` references the patient directly. `DEVICE.S_id` and `URINE_STRIP.S_id` reference a sample. For `REAGENT_PAD`, `D_id` references DEVICE and `S_id` references SAMPLE; there is no composite foreign key enforcing that the selected device belongs to that same sample. The composite primary key includes pad position, sample, and device, since pads are identified within a device/sample. An additional `account` table stores only login data and does not alter clinical relations.

## Stage 2 — design

```text
healthcare_dashboard/
  app/                 Factory, configuration, schema, db helper, blueprints
    auth/              Login, logout, session guard
    main/              Dashboard SQL and overview
    patients/          Patient CRUD and contacts
    doctors/           Doctor and subtype management
    samples/           Sample CRUD and related lab records
    templates/         Shared Jinja base and page templates
    static/            CSS and small confirmation script
  scripts/seed_db.py   Local test account and fictional seed command
  tests/               Flask test client coverage
  instance/            Local SQLite database (ignored by Git)
  run.py               Flask entry point
```

The application factory registers separate auth, overview, patient, doctor, and sample blueprints. SQLite connections live in Flask's `g` for the request and close at app-context teardown. The database helper enables foreign keys on every connection. Login type is recorded and displayed but does not change access. Forms include a session-backed CSRF token checked on every POST.

## Stage 3 — database design and features

All tables are created in dependency order by `flask --app run.py init-db`; this is repeatable and does not drop data. Patient create/edit handles multiple contacts in one transaction. Doctors are linked to an existing patient and exactly one designation subtype through the form. Samples use a database-populated patient dropdown. The sample detail page can add device, urine-strip, and reagent-pad rows; related records keep restrictive delete behavior so dependent data is not silently lost. All SQL values use placeholders.

## Stage 4 — tests

Run the test suite with `pytest`. Tests use a fresh temporary SQLite database and fictional account. They cover factory setup, protected pages, login success/failure, patient validation and creation/listing, logout, and foreign-key enforcement.

## Stage 5 — run locally (Windows PowerShell)

Requires Python 3.10 or newer.

```powershell
cd healthcare_dashboard
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
$env:SECRET_KEY = (py -c "import secrets; print(secrets.token_hex(32))")
flask --app run.py init-db
flask --app run.py seed-db --username demo --password "choose-a-password"
flask --app run.py --debug run
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Sign in with the username and password you chose. The seed command creates one Doctor login and inserts a fictional patient, doctor, sample, device, and strip if the patient table is empty. Choose a new username if running it again. Doctors can also create accounts from the registration link on the sign-in page. The app database defaults to `instance/healthcare.sqlite3`.

To run tests:

```powershell
pytest
```

The `.env.example` file lists supported environment settings, but Flask does not load `.env` automatically; set environment variables in your shell or install/use a dotenv loader. The PowerShell commands above set the secret for the current session. For routine local development the built-in fallback secret works, but use a random `SECRET_KEY` for any shared environment.

## Demonstration path

1. `init-db` creates tables and constraints.
2. Create an account using the registration page, or run `seed-db` to create one Doctor login and fictional relational records. Passwords are stored as Werkzeug hashes.
3. Sign in; `main/routes.py` counts rows with SQL and gives the data to a Jinja template.
4. Submit a patient form; Flask validates fields, inserts patient and contacts with parameterized statements in a transaction, then redirects to the detail route.
5. Register a doctor or sample by selecting a patient populated from SQLite. The database enforces those foreign keys.
6. Add records from a sample detail page and observe how restrictive foreign keys prevent unsafe parent deletion.

The SQL file `app/schema.sql` contains the keys and constraints; `app/db.py` implements the connection and initialization. The project follows Flask's current official factory, blueprint, application-context, configuration, and request-handling guidance: [Application Factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/), [Blueprints](https://flask.palletsprojects.com/en/stable/blueprints/), and [SQLite pattern](https://flask.palletsprojects.com/en/stable/patterns/sqlite3/).


