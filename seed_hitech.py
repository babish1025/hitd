"""Extend database with HODs, Departments, and Settings for HITECH Smart Academic Dashboard."""
import os, sqlite3
import psycopg2
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))

DB_FILE = os.path.join(BASE, "students.db")

SCHEMA_PG_EXTRA = """
CREATE TABLE IF NOT EXISTS hods (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    faculty_id TEXT UNIQUE,
    department TEXT,
    dept_code TEXT,
    mobile TEXT,
    dob TEXT,
    gender TEXT,
    blood_group TEXT,
    photo TEXT DEFAULT '',
    designation TEXT DEFAULT 'Professor & HOD',
    qualification TEXT DEFAULT 'M.E., Ph.D.',
    specialization TEXT DEFAULT 'Cloud & High Performance Computing'
);

CREATE TABLE IF NOT EXISTS departments (
    code TEXT PRIMARY KEY,
    name TEXT,
    hod_name TEXT,
    faculty_count INTEGER DEFAULT 0,
    student_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS college_settings (
    id SERIAL PRIMARY KEY,
    name TEXT,
    address TEXT,
    city TEXT,
    district TEXT,
    state TEXT,
    pincode TEXT,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    phone TEXT,
    email TEXT,
    website TEXT,
    emergency TEXT
);
"""

SCHEMA_SQLITE_EXTRA = """
CREATE TABLE IF NOT EXISTS hods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    faculty_id TEXT UNIQUE,
    department TEXT,
    dept_code TEXT,
    mobile TEXT,
    dob TEXT,
    gender TEXT,
    blood_group TEXT,
    photo TEXT DEFAULT '',
    designation TEXT DEFAULT 'Professor & HOD',
    qualification TEXT DEFAULT 'M.E., Ph.D.',
    specialization TEXT DEFAULT 'Cloud & High Performance Computing'
);

CREATE TABLE IF NOT EXISTS departments (
    code TEXT PRIMARY KEY,
    name TEXT,
    hod_name TEXT,
    faculty_count INTEGER DEFAULT 0,
    student_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS college_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    address TEXT,
    city TEXT,
    district TEXT,
    state TEXT,
    pincode TEXT,
    lat REAL,
    lng REAL,
    phone TEXT,
    email TEXT,
    website TEXT,
    emergency TEXT
);
"""

DEFAULT_HODS = [
    ("Dr. Arun Kumar Senior HOD", "arunkumar@hit.edu.in", "FAC001", "Computer Science & Engineering", "CSE", "9842100001", "1982-05-14", "Male", "O+", "", "Professor & HOD", "M.E., Ph.D.", "Cloud & High Performance Computing"),
    ("Dr. S. Karthik", "karthik@hit.edu.in", "FAC002", "Electronics & Communication Engineering", "ECE", "9842100003", "1980-08-22", "Male", "A+", "", "Professor & HOD", "M.E., Ph.D.", "VLSI & Embedded Systems"),
    ("Dr. Ramesh Babu", "rameshbabu@hit.edu.in", "FAC004", "Artificial Intelligence & Data Science", "AIDS", "9842100004", "1984-11-10", "Male", "B+", "", "Professor & HOD", "M.Tech., Ph.D.", "AI, Machine Learning & Big Data"),
    ("Dr. M. Sangeetha", "sangeetha@hit.edu.in", "FAC005", "Information Technology", "IT", "9842100005", "1986-03-18", "Female", "O+", "", "Professor & HOD", "M.Tech., Ph.D.", "Cyber Security & Networks")
]

DEFAULT_DEPTS = [
    ("CSE", "Computer Science & Engineering", "Dr. Arun Kumar Senior HOD", 18, 63),
    ("ECE", "Electronics & Communication Engineering", "Dr. S. Karthik", 14, 58),
    ("AIDS", "Artificial Intelligence & Data Science", "Dr. Ramesh Babu", 10, 60),
    ("IT", "Information Technology", "Dr. M. Sangeetha", 12, 54)
]

DEFAULT_SETTINGS = (
    1,
    "Hindusthan Institute of Technology",
    "Othakkalmandapam, Pollachi Highway",
    "Coimbatore",
    "Coimbatore",
    "Tamil Nadu",
    "641032",
    10.9008,
    76.9942,
    "+91 422 2930 216",
    "info@hit.edu.in",
    "https://hit.edu.in",
    "+91 422 2611833"
)

def run_migrations():
    # 1. Update SQLite
    c = sqlite3.connect(DB_FILE)
    c.executescript(SCHEMA_SQLITE_EXTRA)
    for h in DEFAULT_HODS:
        c.execute("""
        INSERT OR REPLACE INTO hods (name, email, faculty_id, department, dept_code, mobile, dob, gender, blood_group, photo, designation, qualification, specialization)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, h)
    for d in DEFAULT_DEPTS:
        c.execute("INSERT OR REPLACE INTO departments (code, name, hod_name, faculty_count, student_count) VALUES (?,?,?,?,?)", d)
    c.execute("""
    INSERT OR REPLACE INTO college_settings (id, name, address, city, district, state, pincode, lat, lng, phone, email, website, emergency)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, DEFAULT_SETTINGS)
    c.commit(); c.close()
    print("Local SQLite updated successfully.")

    # 2. Update Supabase
    try:
        host = os.getenv("DB_HOST", "")
        port = int(os.getenv("DB_PORT", 5432))
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        dbname = os.getenv("DB_NAME", "postgres")
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname, sslmode="require", connect_timeout=5)
        cur = conn.cursor()
        cur.execute(SCHEMA_PG_EXTRA)
        for h in DEFAULT_HODS:
            cur.execute("""
            INSERT INTO hods (name, email, faculty_id, department, dept_code, mobile, dob, gender, blood_group, photo, designation, qualification, specialization)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (email) DO UPDATE SET
                name = EXCLUDED.name,
                faculty_id = EXCLUDED.faculty_id,
                department = EXCLUDED.department,
                dept_code = EXCLUDED.dept_code,
                mobile = EXCLUDED.mobile;
            """, h)
        for d in DEFAULT_DEPTS:
            cur.execute("""
            INSERT INTO departments (code, name, hod_name, faculty_count, student_count)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                hod_name = EXCLUDED.hod_name,
                faculty_count = EXCLUDED.faculty_count,
                student_count = EXCLUDED.student_count;
            """, d)
        cur.execute("""
        INSERT INTO college_settings (id, name, address, city, district, state, pincode, lat, lng, phone, email, website, emergency)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            address = EXCLUDED.address,
            phone = EXCLUDED.phone,
            lat = EXCLUDED.lat,
            lng = EXCLUDED.lng;
        """, DEFAULT_SETTINGS)
        conn.commit(); cur.close(); conn.close()
        print("Supabase PostgreSQL updated with HODs, departments & college settings!")
    except Exception as e:
        print(f"Supabase update notice: {e}")

if __name__ == "__main__":
    run_migrations()

