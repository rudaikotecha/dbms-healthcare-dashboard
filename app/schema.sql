CREATE TABLE IF NOT EXISTS patient (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_name TEXT NOT NULL CHECK(length(trim(f_name)) > 0),
    l_name TEXT NOT NULL CHECK(length(trim(l_name)) > 0),
    gender TEXT NOT NULL CHECK(gender IN ('Female','Male','Other','Prefer not to say')),
    dob TEXT NOT NULL CHECK(date(dob) IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS p_contact (
    patient_id INTEGER NOT NULL,
    contact TEXT NOT NULL CHECK(length(trim(contact)) > 0),
    PRIMARY KEY(patient_id, contact),
    FOREIGN KEY(patient_id) REFERENCES patient(patient_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS doctor (
    doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
    department TEXT NOT NULL CHECK(length(trim(department)) > 0),
    p_id INTEGER NOT NULL,
    FOREIGN KEY(p_id) REFERENCES patient(patient_id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS clinician (
    doctor_id INTEGER PRIMARY KEY,
    designation TEXT NOT NULL CHECK(length(trim(designation)) > 0),
    FOREIGN KEY(doctor_id) REFERENCES doctor(doctor_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS consultant (
    doctor_id INTEGER PRIMARY KEY,
    designation TEXT NOT NULL CHECK(length(trim(designation)) > 0),
    FOREIGN KEY(doctor_id) REFERENCES doctor(doctor_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sample (
    sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reaction_status TEXT NOT NULL CHECK(length(trim(reaction_status)) > 0),
    collection_time TEXT NOT NULL,
    p_id INTEGER NOT NULL,
    FOREIGN KEY(p_id) REFERENCES patient(patient_id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS device (
    device_id INTEGER PRIMARY KEY AUTOINCREMENT,
    calibration_date TEXT NOT NULL CHECK(date(calibration_date) IS NOT NULL),
    s_id INTEGER NOT NULL,
    FOREIGN KEY(s_id) REFERENCES sample(sample_id) ON DELETE RESTRICT,
    UNIQUE(device_id, s_id)
);
CREATE TABLE IF NOT EXISTS urine_strip (
    manufacturer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_name TEXT NOT NULL CHECK(length(trim(manufacturer_name)) > 0),
    s_id INTEGER NOT NULL,
    FOREIGN KEY(s_id) REFERENCES sample(sample_id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS reagent_pad (
    pad_position INTEGER NOT NULL,
    s_id INTEGER NOT NULL,
    d_id INTEGER NOT NULL,
    red_value INTEGER NOT NULL CHECK(red_value BETWEEN 0 AND 255),
    green_value INTEGER NOT NULL CHECK(green_value BETWEEN 0 AND 255),
    blue_value INTEGER NOT NULL CHECK(blue_value BETWEEN 0 AND 255),
    analyte TEXT NOT NULL CHECK(length(trim(analyte)) > 0),
    PRIMARY KEY(pad_position, s_id, d_id),
    FOREIGN KEY(s_id) REFERENCES sample(sample_id) ON DELETE RESTRICT,
    FOREIGN KEY(d_id, s_id) REFERENCES device(device_id, s_id) ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS account (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    login_type TEXT NOT NULL CHECK(login_type = 'Doctor')
);
