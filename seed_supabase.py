"""Seed Supabase PostgreSQL and SQLite DB from students.xlsx."""
import os, sys, math
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))

XLSX = os.path.join(BASE, "students.xlsx")

SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS students (
    reg_no TEXT PRIMARY KEY,
    name TEXT,
    aadhar TEXT,
    dob TEXT,
    gender TEXT,
    quota TEXT,
    blood_group TEXT,
    community TEXT,
    day_hos TEXT,
    whatsapp TEXT,
    personal_no TEXT,
    father TEXT,
    father_mob TEXT,
    mother TEXT,
    mother_mob TEXT,
    addr1 TEXT,
    addr2 TEXT,
    addr3 TEXT,
    addr4 TEXT,
    addr5 TEXT,
    pincode TEXT,
    attendance DOUBLE PRECISION DEFAULT 0,
    cgpa DOUBLE PRECISION DEFAULT 0,
    state TEXT,
    district TEXT,
    photo TEXT DEFAULT '',
    password TEXT
);

CREATE TABLE IF NOT EXISTS marksheets (
    id SERIAL PRIMARY KEY,
    reg_no TEXT,
    semester INTEGER,
    filename TEXT,
    uploaded_at TEXT,
    UNIQUE(reg_no, semester)
);

CREATE TABLE IF NOT EXISTS professors (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE,
    name TEXT,
    photo TEXT DEFAULT ''
);
"""

def clean(v):
    if v is None: return ""
    if isinstance(v, float) and math.isnan(v): return ""
    return str(v).strip()

def get_pg_connection():
    db_host = os.getenv("DB_HOST", "")
    db_port = int(os.getenv("DB_PORT", 5432))
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "postgres")
    return psycopg2.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_pass,
        dbname=db_name,
        sslmode="require"
    )

def seed_supabase():
    print("Connecting to Supabase PostgreSQL at ap-northeast-2...")
    conn = get_pg_connection()
    cur = conn.cursor()
    
    print("Creating tables in Supabase public schema...")
    cur.execute(SCHEMA_PG)
    conn.commit()

    print(f"Reading students from {XLSX}...")
    df = pd.read_excel(XLSX, sheet_name="25 CSE A ALL DETAILS ")
    df.columns = [c.strip() for c in df.columns]
    
    student_count = 0
    for _, r in df.iterrows():
        reg = clean(r.get("REG NO"))
        if not reg or not reg.isdigit():
            continue
        dob = r.get("STUDENT  D O B")
        try:
            dob = pd.to_datetime(dob).strftime("%Y-%m-%d")
        except:
            dob = ""
        attn = r.get("Attn %")
        attn = float(attn) if pd.notna(attn) else 0.0
        cgpa = r.get("cgpa")
        cgpa = float(cgpa) if pd.notna(cgpa) else 0.0
        
        insert_sql = """
        INSERT INTO students (
            reg_no, name, aadhar, dob, gender, quota,
            blood_group, community, day_hos, whatsapp, personal_no,
            father, father_mob, mother, mother_mob,
            addr1, addr2, addr3, addr4, addr5,
            pincode, attendance, cgpa, state, district,
            photo, password
        ) VALUES (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
        )
        ON CONFLICT (reg_no) DO UPDATE SET
            name = EXCLUDED.name,
            aadhar = EXCLUDED.aadhar,
            dob = EXCLUDED.dob,
            gender = EXCLUDED.gender,
            quota = EXCLUDED.quota,
            blood_group = EXCLUDED.blood_group,
            community = EXCLUDED.community,
            day_hos = EXCLUDED.day_hos,
            whatsapp = EXCLUDED.whatsapp,
            personal_no = EXCLUDED.personal_no,
            father = EXCLUDED.father,
            father_mob = EXCLUDED.father_mob,
            mother = EXCLUDED.mother,
            mother_mob = EXCLUDED.mother_mob,
            addr1 = EXCLUDED.addr1,
            addr2 = EXCLUDED.addr2,
            addr3 = EXCLUDED.addr3,
            addr4 = EXCLUDED.addr4,
            addr5 = EXCLUDED.addr5,
            pincode = EXCLUDED.pincode,
            attendance = EXCLUDED.attendance,
            cgpa = EXCLUDED.cgpa,
            state = EXCLUDED.state,
            district = EXCLUDED.district;
        """
        vals = (
            reg, clean(r.get("STUDENT NAME")), clean(r.get("AADHAR NO")),
            dob, clean(r.get("GENDER")), clean(r.get("QUOTA")),
            clean(r.get("Blood group")), clean(r.get("COMMUNITY")),
            clean(r.get("DAY/HOS")), clean(r.get("WHATS APP NO")),
            clean(r.get("PER  NO")), clean(r.get("FATHER NAME")),
            clean(r.get("F MOB NO")), clean(r.get("MOTHER  NAME")),
            clean(r.get("M  MOB NO")), clean(r.get("ADDRESS  LINE NO 1")),
            clean(r.get("ADDRESS  LINE NO  2")), clean(r.get("ADDRESS  LINE 3")),
            clean(r.get("ADDRESS  LINE 4")), clean(r.get("ADDRESS  LINE 5")),
            clean(r.get("PINCODE")), attn, cgpa,
            clean(r.get("STATES")), clean(r.get("DISTRICT")),
            "", reg[-6:]
        )
        cur.execute(insert_sql, vals)
        student_count += 1
        
    faculty = [
        ("vijayalakshmi@hit.edu.in", "Dr. V. Vijayalakshmi"),
        ("suganya@hit.edu.in", "Mrs. S. Suganya"),
        ("senthilkumar@hit.edu.in", "Dr. R. Senthilkumar"),
        ("praveena@hit.edu.in", "Dr. R. Praveena"),
        ("priyanka@hit.edu.in", "Mrs. V. Priyanka"),
        ("jayaprakash@hit.edu.in", "Mr. S. Jayaprakash"),
        ("vignesh@hit.edu.in", "Mr. K. Vignesh"),
    ]
    for email, name in faculty:
        cur.execute("""
        INSERT INTO professors(email, name, photo)
        VALUES (%s, %s, '')
        ON CONFLICT (email) DO NOTHING;
        """, (email, name))
        
    conn.commit()
    cur.close()
    conn.close()
    print(f"Successfully seeded {student_count} students and {len(faculty)} professors to Supabase PostgreSQL!")

if __name__ == "__main__":
    seed_supabase()

