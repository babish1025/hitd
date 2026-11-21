"""Database layer for HIT CSE-A / HITECH Smart Academic Dashboard.
Primary: Supabase Cloud Database (REST)
Fallback: Local SQLite (students.db)
"""
import os, sqlite3
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))

DB_FILE = os.path.join(BASE, "students.db")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
_supabase_client = None

def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return None
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"[Supabase Init Warning] {e}")
            _supabase_client = None
    return _supabase_client

class Database:
    """Unified database operations with Add, Edit, Delete for Faculty, HOD, and Admin."""

    # ==================== STUDENTS ====================
    @staticmethod
    def get_all_students(order_by="reg_no"):
        sb = get_supabase()
        if sb:
            try:
                res = sb.table("students").select("*").order(order_by).execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[Supabase Query Error] get_all_students: {e}")
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute(f"SELECT * FROM students ORDER BY {order_by}").fetchall()]
        c.close(); return rows

    @staticmethod
    def get_student_by_reg(reg_no):
        reg = str(reg_no).strip()
        sb = get_supabase()
        if sb:
            try:
                res = sb.table("students").select("*").eq("reg_no", reg).limit(1).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[Supabase Query Error] get_student_by_reg: {e}")
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        s = c.execute("SELECT * FROM students WHERE reg_no=?", (reg,)).fetchone()
        c.close(); return dict(s) if s else None

    @staticmethod
    def add_student(data):
        """Add new student to both Supabase and SQLite."""
        reg = str(data.get("reg_no", "")).strip()
        name = data.get("name", "").strip()
        pwd = data.get("password") or (reg[-6:] if len(reg) >= 6 else "123456")
        
        student_obj = {
            "reg_no": reg,
            "name": name,
            "dob": data.get("dob", ""),
            "gender": data.get("gender", "Male"),
            "aadhar": data.get("aadhar", ""),
            "blood_group": data.get("blood_group", ""),
            "quota": data.get("quota", "Government"),
            "community": data.get("community", ""),
            "day_hos": data.get("day_hos", "Day Scholar"),
            "whatsapp": data.get("whatsapp", ""),
            "personal_no": data.get("personal_no", ""),
            "father": data.get("father", ""),
            "father_mob": data.get("father_mob", ""),
            "mother": data.get("mother", ""),
            "mother_mob": data.get("mother_mob", ""),
            "addr1": data.get("addr1", ""),
            "addr2": data.get("addr2", ""),
            "addr3": data.get("addr3", ""),
            "addr4": data.get("addr4", ""),
            "addr5": data.get("addr5", ""),
            "district": data.get("district", "Coimbatore"),
            "state": data.get("state", "Tamil Nadu"),
            "pincode": data.get("pincode", ""),
            "attendance": float(data.get("attendance") or 0.0),
            "cgpa": float(data.get("cgpa") or 0.0),
            "password": pwd,
            "photo": data.get("photo", "")
        }

        sb = get_supabase()
        if sb:
            try:
                sb.table("students").insert(student_obj).execute()
            except Exception as e:
                print(f"[Supabase Insert Error] add_student: {e}")

        try:
            c = sqlite3.connect(DB_FILE)
            c.execute("""
            INSERT OR REPLACE INTO students (
                reg_no, name, dob, gender, aadhar, blood_group, quota, community, day_hos,
                whatsapp, personal_no, father, father_mob, mother, mother_mob,
                addr1, addr2, addr3, addr4, addr5, district, state, pincode,
                attendance, cgpa, password, photo
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                student_obj["reg_no"], student_obj["name"], student_obj["dob"], student_obj["gender"],
                student_obj["aadhar"], student_obj["blood_group"], student_obj["quota"], student_obj["community"],
                student_obj["day_hos"], student_obj["whatsapp"], student_obj["personal_no"],
                student_obj["father"], student_obj["father_mob"], student_obj["mother"], student_obj["mother_mob"],
                student_obj["addr1"], student_obj["addr2"], student_obj["addr3"], student_obj["addr4"], student_obj["addr5"],
                student_obj["district"], student_obj["state"], student_obj["pincode"],
                student_obj["attendance"], student_obj["cgpa"], student_obj["password"], student_obj["photo"]
            ))
            c.commit(); c.close()
        except Exception as e:
            print(f"[SQLite Insert Error] add_student: {e}")

    @staticmethod
    def update_student(reg_no, data):
        """Edit / Update existing student in both Supabase and SQLite."""
        reg = str(reg_no).strip()
        update_fields = {}
        for k in ["name", "dob", "gender", "aadhar", "blood_group", "quota", "community", "day_hos",
                  "whatsapp", "personal_no", "father", "father_mob", "mother", "mother_mob",
                  "addr1", "addr2", "addr3", "addr4", "addr5", "district", "state", "pincode", "password"]:
            if k in data and data[k] is not None:
                update_fields[k] = data[k]
        
        if "attendance" in data and data["attendance"] is not None:
            try: update_fields["attendance"] = float(data["attendance"])
            except: pass
        if "cgpa" in data and data["cgpa"] is not None:
            try: update_fields["cgpa"] = float(data["cgpa"])
            except: pass

        sb = get_supabase()
        if sb:
            try:
                sb.table("students").update(update_fields).eq("reg_no", reg).execute()
            except Exception as e:
                print(f"[Supabase Update Error] update_student: {e}")

        try:
            c = sqlite3.connect(DB_FILE)
            set_clauses = [f"{k}=?" for k in update_fields.keys()]
            vals = list(update_fields.values()) + [reg]
            c.execute(f"UPDATE students SET {', '.join(set_clauses)} WHERE reg_no=?", vals)
            c.commit(); c.close()
        except Exception as e:
            print(f"[SQLite Update Error] update_student: {e}")

    @staticmethod
    def delete_student(reg_no):
        """Delete student from both Supabase and SQLite."""
        reg = str(reg_no).strip()
        sb = get_supabase()
        if sb:
            try:
                sb.table("students").delete().eq("reg_no", reg).execute()
            except Exception as e:
                print(f"[Supabase Delete Error] delete_student: {e}")

        try:
            c = sqlite3.connect(DB_FILE)
            c.execute("DELETE FROM students WHERE reg_no=?", (reg,))
            c.execute("DELETE FROM marksheets WHERE reg_no=?", (reg,))
            c.commit(); c.close()
        except Exception as e:
            print(f"[SQLite Delete Error] delete_student: {e}")

    @staticmethod
    def update_student_photo(reg_no, filename):
        reg = str(reg_no).strip()
        sb = get_supabase()
        if sb:
            try:
                sb.table("students").update({"photo": filename}).eq("reg_no", reg).execute()
            except Exception as e:
                print(f"[Supabase Query Error] update_student_photo: {e}")
        try:
            c = sqlite3.connect(DB_FILE)
            c.execute("UPDATE students SET photo=? WHERE reg_no=?", (filename, reg))
            c.commit(); c.close()
        except: pass

    # ==================== FACULTY ====================
    @staticmethod
    def get_all_professors():
        sb = get_supabase()
        if sb:
            try:
                res = sb.table("professors").select("*").execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[Supabase Query Error] get_all_professors: {e}")
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute("SELECT * FROM professors").fetchall()]
        c.close(); return rows

    @staticmethod
    def add_faculty(name, email, photo="", extra=None):
        em = email.lower().strip()
        extra = extra or {}
        mobile = extra.get("mobile","")
        designation = extra.get("designation","Assistant Professor")
        department = extra.get("department","CSE")
        qualification = extra.get("qualification","")
        specialization = extra.get("specialization","")
        sb = get_supabase()
        if sb:
            try:
                sb.table("professors").insert({
                    "name": name, "email": em, "photo": photo,
                    "mobile": mobile, "designation": designation,
                    "department": department, "qualification": qualification,
                    "specialization": specialization
                }).execute()
            except Exception as e:
                print(f"[Supabase Insert Error] add_faculty: {e}")
        try:
            c = sqlite3.connect(DB_FILE)
            c.execute("INSERT OR REPLACE INTO professors(name, email, photo) VALUES(?,?,?)", (name, em, photo))
            c.commit(); c.close()
        except: pass

    @staticmethod
    def update_faculty(fid, name, email, extra=None):
        em = email.lower().strip()
        extra = extra or {}
        mobile = extra.get("mobile","")
        designation = extra.get("designation","")
        department = extra.get("department","")
        qualification = extra.get("qualification","")
        specialization = extra.get("specialization","")
        sb = get_supabase()
        if sb:
            try:
                sb.table("professors").update({
                    "name": name, "email": em,
                    "mobile": mobile, "designation": designation,
                    "department": department, "qualification": qualification,
                    "specialization": specialization
                }).eq("id", fid).execute()
            except Exception as e:
                print(f"[Supabase Update Error] update_faculty: {e}")
        try:
            c = sqlite3.connect(DB_FILE)
            c.execute("UPDATE professors SET name=?, email=? WHERE id=?", (name, em, fid))
            c.commit(); c.close()
        except: pass

    @staticmethod
    def delete_faculty(fid):
        sb = get_supabase()
        if sb:
            try:
                sb.table("professors").delete().eq("id", fid).execute()
            except Exception as e:
                print(f"[Supabase Delete Error] delete_faculty: {e}")
        try:
            c = sqlite3.connect(DB_FILE)
            c.execute("DELETE FROM professors WHERE id=?", (fid,))
            c.commit(); c.close()
        except: pass

    @staticmethod
    def get_professor_by_email(email):
        em = email.lower().strip()
        sb = get_supabase()
        if sb:
            try:
                res = sb.table("professors").select("*").eq("email", em).limit(1).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[Supabase Query Error] get_professor_by_email: {e}")
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        p = c.execute("SELECT * FROM professors WHERE email=?", (em,)).fetchone()
        c.close(); return dict(p) if p else None

    @staticmethod
    def insert_professor_if_not_exists(email, name):
        em = email.lower().strip()
        sb = get_supabase()
        if sb:
            try:
                res = sb.table("professors").select("*").eq("email", em).limit(1).execute()
                if not res.data:
                    sb.table("professors").insert({"email": em, "name": name, "photo": ""}).execute()
            except Exception as e:
                print(f"[Supabase Query Error] insert_professor: {e}")
        try:
            c = sqlite3.connect(DB_FILE)
            p = c.execute("SELECT * FROM professors WHERE email=?", (em,)).fetchone()
            if not p:
                c.execute("INSERT INTO professors(email, name, photo) VALUES(?,?,?)", (em, name, ""))
                c.commit()
            c.close()
        except: pass

    @staticmethod
    def update_professor_photo(email, filename):
        em = email.lower().strip()
        sb = get_supabase()
        if sb:
            try:
                sb.table("professors").update({"photo": filename}).eq("email", em).execute()
            except Exception as e:
                print(f"[Supabase Query Error] update_professor_photo: {e}")
        try:
            c = sqlite3.connect(DB_FILE)
            c.execute("UPDATE professors SET photo=? WHERE email=?", (filename, em))
            c.commit(); c.close()
        except: pass

    # ==================== HODS ====================
    @staticmethod
    def get_all_hods():
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute("SELECT * FROM hods ORDER BY id").fetchall()]
        c.close(); return rows

    @staticmethod
    def get_hod_by_id(hid):
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        row = c.execute("SELECT * FROM hods WHERE id=?", (hid,)).fetchone()
        c.close(); return dict(row) if row else None

    @staticmethod
    def add_hod(data):
        c = sqlite3.connect(DB_FILE)
        c.execute("""
        INSERT INTO hods (name, email, faculty_id, department, dept_code, mobile, dob, gender, blood_group, photo, designation, qualification, specialization)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("name"), data.get("email"), data.get("faculty_id"), data.get("department"),
            data.get("dept_code"), data.get("mobile"), data.get("dob", "1980-01-01"), data.get("gender", "Male"),
            data.get("blood_group", "O+"), "", data.get("designation", "Professor & HOD"),
            data.get("qualification", "M.E., Ph.D."), data.get("specialization", "")
        ))
        c.commit(); c.close()

    @staticmethod
    def update_hod(hid, data):
        c = sqlite3.connect(DB_FILE)
        c.execute("""
        UPDATE hods SET name=?, email=?, faculty_id=?, department=?, dept_code=?, mobile=?, designation=?, qualification=?, specialization=?
        WHERE id=?
        """, (
            data.get("name"), data.get("email"), data.get("faculty_id"), data.get("department"),
            data.get("dept_code"), data.get("mobile"), data.get("designation"),
            data.get("qualification"), data.get("specialization"), hid
        ))
        c.commit(); c.close()

    @staticmethod
    def delete_hod(hid):
        c = sqlite3.connect(DB_FILE)
        c.execute("DELETE FROM hods WHERE id=?", (hid,))
        c.commit(); c.close()

    # ==================== DEPARTMENTS ====================
    @staticmethod
    def get_all_departments():
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute("SELECT * FROM departments ORDER BY code").fetchall()]
        c.close(); return rows

    # ==================== COLLEGE SETTINGS ====================
    @staticmethod
    def get_college_settings():
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        row = c.execute("SELECT * FROM college_settings WHERE id=1").fetchone()
        c.close()
        if row: return dict(row)
        return {
            "name": "Hindusthan Institute of Technology",
            "address": "Othakkalmandapam, Pollachi Highway",
            "city": "Coimbatore",
            "district": "Coimbatore",
            "state": "Tamil Nadu",
            "pincode": "641032",
            "lat": 10.9008,
            "lng": 76.9942,
            "phone": "+91 422 2930 216",
            "email": "info@hit.edu.in",
            "website": "https://hit.edu.in",
            "emergency": "+91 422 2611833"
        }

    @staticmethod
    def update_college_settings(data):
        c = sqlite3.connect(DB_FILE)
        c.execute("""
        UPDATE college_settings SET
            name=?, address=?, city=?, district=?, state=?, pincode=?,
            lat=?, lng=?, phone=?, email=?, website=?, emergency=?
        WHERE id=1
        """, (
            data.get("name"), data.get("address"), data.get("city"),
            data.get("district"), data.get("state"), data.get("pincode"),
            float(data.get("lat") or 10.9008), float(data.get("lng") or 76.9942),
            data.get("phone"), data.get("email"), data.get("website"), data.get("emergency")
        ))
        c.commit(); c.close()

    # ==================== MARKSHEETS ====================
    @staticmethod
    def get_all_marksheets():
        sb = get_supabase()
        if sb:
            try:
                res = sb.table("marksheets").select("*").execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[Supabase Query Error] get_all_marksheets: {e}")
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute("SELECT * FROM marksheets").fetchall()]
        c.close(); return rows

    @staticmethod
    def get_student_marksheets(reg_no):
        reg = str(reg_no).strip()
        sb = get_supabase()
        if sb:
            try:
                res = sb.table("marksheets").select("*").eq("reg_no", reg).order("semester").execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[Supabase Query Error] get_student_marksheets: {e}")
        c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute("SELECT * FROM marksheets WHERE reg_no=? ORDER BY semester", (reg,)).fetchall()]
        c.close(); return rows

    @staticmethod
    def save_marksheet(reg_no, semester, filename, uploaded_at):
        reg = str(reg_no).strip()
        sb = get_supabase()
        if sb:
            try:
                res = sb.table("marksheets").select("*").eq("reg_no", reg).eq("semester", semester).execute()
                if res.data:
                    sb.table("marksheets").update({"filename": filename, "uploaded_at": uploaded_at}).eq("reg_no", reg).eq("semester", semester).execute()
                else:
                    sb.table("marksheets").insert({"reg_no": reg, "semester": semester, "filename": filename, "uploaded_at": uploaded_at}).execute()
            except Exception as e:
                print(f"[Supabase Query Error] save_marksheet: {e}")
        try:
            c = sqlite3.connect(DB_FILE)
            c.execute("INSERT OR REPLACE INTO marksheets(reg_no,semester,filename,uploaded_at) VALUES(?,?,?,?)",
                      (reg, semester, filename, uploaded_at))
            c.commit(); c.close()
        except: pass
