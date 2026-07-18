"""Seed SQLite DB from the class Excel spreadsheet."""
import sqlite3, os, math
import pandas as pd

DB = os.path.join(os.path.dirname(__file__), "students.db")
XLSX = os.path.join(os.path.dirname(__file__), "students.xlsx")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    reg_no TEXT PRIMARY KEY,
    name TEXT, aadhar TEXT, dob TEXT, gender TEXT, quota TEXT,
    blood_group TEXT, community TEXT, day_hos TEXT,
    whatsapp TEXT, personal_no TEXT,
    father TEXT, father_mob TEXT, mother TEXT, mother_mob TEXT,
    addr1 TEXT, addr2 TEXT, addr3 TEXT, addr4 TEXT, addr5 TEXT,
    pincode TEXT, attendance REAL, cgpa REAL,
    state TEXT, district TEXT,
    photo TEXT, password TEXT
);
CREATE TABLE IF NOT EXISTS marksheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_no TEXT, semester INTEGER, filename TEXT,
    uploaded_at TEXT, UNIQUE(reg_no, semester)
);
CREATE TABLE IF NOT EXISTS professors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE, name TEXT, photo TEXT
);
"""

def clean(v):
    if v is None: return ""
    if isinstance(v, float) and math.isnan(v): return ""
    return str(v).strip()

def main():
    if os.path.exists(DB): os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    df = pd.read_excel(XLSX, sheet_name="25 CSE A ALL DETAILS ")
    df.columns = [c.strip() for c in df.columns]
    for _, r in df.iterrows():
        reg = clean(r.get("REG NO"))
        if not reg or not reg.isdigit(): continue
        dob = r.get("STUDENT  D O B")
        try: dob = pd.to_datetime(dob).strftime("%Y-%m-%d")
        except: dob = ""
        attn = r.get("Attn %"); attn = float(attn) if pd.notna(attn) else 0
        cgpa = r.get("cgpa"); cgpa = float(cgpa) if pd.notna(cgpa) else 0
        con.execute("""INSERT OR REPLACE INTO students VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
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
            "", reg[-6:]  # default password = last 6 of reg no
        ))
    # seed professors from timetable image
    faculty = [
        ("vijayalakshmi@hit.edu.in", "Dr. V. Vijayalakshmi"),
        ("suganya@hit.edu.in", "Mrs. S. Suganya"),
        ("senthilkumar@hit.edu.in", "Dr. R. Senthilkumar"),
        ("praveena@hit.edu.in", "Dr. R. Praveena"),
        ("priyanka@hit.edu.in", "Mrs. V. Priyanka"),
        ("jayaprakash@hit.edu.in", "Mr. S. Jayaprakash"),
        ("vignesh@hit.edu.in", "Mr. K. Vignesh"),
    ]
    for e, n in faculty:
        con.execute("INSERT OR IGNORE INTO professors(email,name,photo) VALUES(?,?,?)", (e, n, ""))
    con.commit(); con.close()
    print("Seeded", DB)

if __name__ == "__main__":
    main()
