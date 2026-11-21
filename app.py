"""HITECH — HIT Smart Academic Dashboard | Command & Intelligence System
Flask backend supporting Admin, HOD, Faculty, and Student portals with Supabase PostgreSQL.
"""
import os, datetime, urllib.parse
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template, jsonify, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))

from database import Database

UPLOAD_PHOTOS = os.path.join(BASE, "static", "uploads", "photos")
UPLOAD_MARKS = os.path.join(BASE, "static", "uploads", "marksheets")
os.makedirs(UPLOAD_PHOTOS, exist_ok=True)
os.makedirs(UPLOAD_MARKS, exist_ok=True)

PROFESSOR_PASSWORD = os.getenv("PROFESSOR_PASSWORD", "HIT2026")
ADMIN_PASSWORD     = os.getenv("ADMIN_PASSWORD")          # set in .env — no hardcoded fallback
PROF_EMAIL_DOMAIN  = "@hit.edu.in"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")

# ---------- Timetable (from class timetable) ----------
TIMETABLE = {
    "Monday":    ["24TP703","24TP703","24AD401","24CS401","24TP703","24TP703","24TP703"],
    "Tuesday":   ["24AD401","24AD401","24CS401","24CS401","24MA204","LIB","24CS401"],
    "Wednesday": ["24IT401","24EC303","24TP703","24TP703","24EC303","24EC303","24EC303"],
    "Thursday":  ["24CS402","24CS402","24MA204","24IT401","24EC303","24CS402","24AD401"],
    "Friday":    ["24EC303","24IT401","24IT401","24IT401","24CS401","24CS402","24CS402"],
    "Saturday":  ["24CS401","24MA204","TWM","24AD401","24IT401","24EC303","24MC803"],
}
PERIODS = ["9.15-10.05","10.05-10.55","11.15-12.05","12.05-12.55","2.00-2.50","2.50-3.40","3.40-4.30"]
SUBJECTS = {
    "24MA204": {"name":"Discrete Mathematics","hours":5,"faculty":"Dr. V. Vijayalakshmi","email":"vijayalakshmi@hit.edu.in","kind":"Theory"},
    "24EC303": {"name":"Digital Principles and Computer Organization","hours":4,"faculty":"Mrs. S. Suganya","email":"suganya@hit.edu.in","kind":"Theory"},
    "24IT401": {"name":"Java Programming","hours":4,"faculty":"Dr. R. Senthilkumar","email":"senthilkumar@hit.edu.in","kind":"Theory"},
    "24CS401": {"name":"Data Structures II","hours":4,"faculty":"Dr. R. Praveena","email":"praveena@hit.edu.in","kind":"Theory"},
    "24AD401": {"name":"Clean Coding and Devops","hours":3,"faculty":"Mrs. V. Priyanka","email":"priyanka@hit.edu.in","kind":"Theory"},
    "24MC803": {"name":"Essence of Indian Traditional Knowledge","hours":2,"faculty":"Mr. S. Jayaprakash","email":"jayaprakash@hit.edu.in","kind":"Theory"},
    "24TP703": {"name":"Soft Skills & Aptitude - III","hours":2,"faculty":"Mr. K. Vignesh","email":"vignesh@hit.edu.in","kind":"Placement"},
    "24CS402": {"name":"Web Programming I","hours":2,"faculty":"Dr. R. Senthilkumar","email":"senthilkumar@hit.edu.in","kind":"Theory/Practical"},
    "TWM":     {"name":"Tutor Ward Meeting","hours":1,"faculty":"Mrs. A. Praveena","email":"praveena@hit.edu.in","kind":"General"},
    "LIB":     {"name":"Library","hours":1,"faculty":"Mrs. A. Praveena","email":"praveena@hit.edu.in","kind":"General"},
}

# ---------- Auth helpers ----------
def require_any(roles):
    def deco(fn):
        @wraps(fn)
        def wrap(*a, **k):
            if session.get("role") not in roles:
                return redirect(url_for("login"))
            return fn(*a, **k)
        return wrap
    return deco

# ---------- Public & Auth Routes ----------
@app.route("/")
def login():
    role = session.get("role")
    if role == "student":
        return redirect(url_for("student"))
    if role in ["admin", "hod", "faculty", "professor"]:
        return redirect(url_for("admin_dashboard"))
    return render_template("login.html")

@app.post("/login")
def do_login():
    role = request.form.get("role", "admin").lower()
    pwd = request.form.get("password", "")

    if role == "admin":
        user = request.form.get("email", "").strip()
        if pwd in [ADMIN_PASSWORD, PROFESSOR_PASSWORD]:
            session["role"] = "admin"
            session["email"] = "admin@hit.edu.in"
            session["name"] = "admin (ADMIN)"
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials.", "err")
            return redirect(url_for("login"))

    elif role in ["hod", "faculty", "professor"]:
        email = request.form.get("email", "").strip().lower()
        if not email.endswith(PROF_EMAIL_DOMAIN) and not email.startswith("admin"):
            flash("Institutional email must end with @hit.edu.in", "err")
            return redirect(url_for("login"))
        if pwd != PROFESSOR_PASSWORD and pwd != ADMIN_PASSWORD:
            flash(f"Invalid password for {role.upper()}.", "err")
            return redirect(url_for("login"))
        
        prof = Database.get_professor_by_email(email)
        if not prof:
            name = email.split("@")[0].title()
            Database.insert_professor_if_not_exists(email, name)
            prof = {"name": name, "email": email}

        session["role"] = role
        session["email"] = email
        session["name"] = prof.get("name", "Faculty Member")
        return redirect(url_for("admin_dashboard"))

    else:
        # Student Login
        reg = request.form.get("reg_no", "").strip()
        s = Database.get_student_by_reg(reg)
        if not s or s.get("password") != pwd:
            flash("Invalid Register Number or Password.", "err")
            return redirect(url_for("login"))
        session["role"] = "student"
        session["reg_no"] = reg
        session["name"] = s.get("name", "Student")
        return redirect(url_for("student"))

@app.route("/forgot")
def forgot():
    role = request.args.get("role", "student")
    who = request.args.get("who", "").strip()
    if role == "student":
        s = Database.get_student_by_reg(who)
        if not s or not s.get("whatsapp"):
            flash("No WhatsApp number on record for that Register Number.", "err")
            return redirect(url_for("login"))
        msg = f"Hello {s['name']}, your HIT Smart Academic password is: {s['password']}"
        wa = f"https://wa.me/91{s['whatsapp']}?text={urllib.parse.quote(msg)}"
        return redirect(wa)
    else:
        flash(f"Staff password is fixed by institution: {PROFESSOR_PASSWORD}", "info")
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- Admin & Command Center ----------
@app.route("/admin")
@app.route("/admin/students")
@app.route("/admin/college-location")
@app.route("/admin/profiles")
@app.route("/professor")
@require_any(["admin", "hod", "faculty", "professor"])
def admin_dashboard():
    students = Database.get_all_students(order_by="reg_no")
    profs = Database.get_all_professors()
    hods = Database.get_all_hods()
    departments = Database.get_all_departments()
    settings = Database.get_college_settings()
    marks = Database.get_all_marksheets()
    stats = _stats(students)
    birthdays = _todays_birthdays(students)
    
    return render_template("admin_dashboard.html",
        students=students, professors=profs, hods=hods, departments=departments,
        settings=settings, marksheets=marks, stats=stats, birthdays=birthdays,
        timetable=TIMETABLE, periods=PERIODS, subjects=SUBJECTS,
        user_role=session.get("role", "admin"), user_name=session.get("name", "Administrator"))

@app.post("/admin/save_settings")
@require_any(["admin", "hod"])
def save_settings():
    Database.update_college_settings(request.form)
    flash("Institution coordinates and contact channels saved successfully.", "info")
    return redirect(url_for("admin_dashboard"))

# ---------- Student CRUD (Faculty, HOD, Admin only) ----------
@app.post("/admin/students/add")
@require_any(["admin", "hod", "faculty", "professor"])
def add_student():
    data = dict(request.form)
    reg = data.get("reg_no", "").strip()
    if not reg:
        flash("Register number is required.", "err")
        return redirect(url_for("admin_dashboard"))
    existing = Database.get_student_by_reg(reg)
    if existing:
        flash(f"Student with Register Number {reg} already exists.", "err")
        return redirect(url_for("admin_dashboard"))
    Database.add_student(data)
    flash(f"Student {data.get('name')} ({reg}) added successfully.", "info")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/students/edit/<reg_no>")
@require_any(["admin", "hod", "faculty", "professor"])
def edit_student(reg_no):
    data = dict(request.form)
    Database.update_student(reg_no, data)
    flash(f"Student {reg_no} details updated successfully.", "info")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/students/delete/<reg_no>")
@require_any(["admin", "hod", "faculty", "professor"])
def delete_student(reg_no):
    Database.delete_student(reg_no)
    flash(f"Student {reg_no} has been removed from the institutional database.", "info")
    return redirect(url_for("admin_dashboard"))

# ---------- Faculty CRUD ----------
@app.post("/admin/faculty/add")
@require_any(["admin", "hod"])
def add_faculty():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    if not name or not email:
        flash("Faculty name and email are required.", "err")
        return redirect(url_for("admin_dashboard"))
    Database.add_faculty(name, email, extra=dict(request.form))
    flash(f"Faculty {name} added.", "info")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/faculty/edit/<int:fid>")
@require_any(["admin", "hod"])
def edit_faculty(fid):
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    Database.update_faculty(fid, name, email, extra=dict(request.form))
    flash("Faculty updated.", "info")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/faculty/delete/<int:fid>")
@require_any(["admin", "hod"])
def delete_faculty(fid):
    Database.delete_faculty(fid)
    flash("Faculty member removed.", "info")
    return redirect(url_for("admin_dashboard"))

# ---------- HOD CRUD ----------
@app.post("/admin/hod/add")
@require_any(["admin"])
def add_hod():
    Database.add_hod(dict(request.form))
    flash("New HOD profile created.", "info")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/hod/edit/<int:hid>")
@require_any(["admin"])
def edit_hod(hid):
    Database.update_hod(hid, dict(request.form))
    flash("HOD profile updated.", "info")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/hod/delete/<int:hid>")
@require_any(["admin"])
def delete_hod(hid):
    Database.delete_hod(hid)
    flash("HOD profile deleted.", "info")
    return redirect(url_for("admin_dashboard"))

# ---------- Photo & Marksheet Uploads ----------
@app.post("/professor/upload_photo/<reg_no>")
@require_any(["admin", "hod", "faculty", "professor"])
def upload_photo(reg_no):
    f = request.files.get("photo")
    if not f or not f.filename:
        flash("No file selected.", "err")
        return redirect(url_for("admin_dashboard"))
    fn = secure_filename(f"{reg_no}_{f.filename}")
    f.save(os.path.join(UPLOAD_PHOTOS, fn))
    Database.update_student_photo(reg_no, fn)
    flash("Student photo updated canonical sync.", "info")
    return redirect(url_for("admin_dashboard"))

@app.post("/professor/upload_marksheet/<reg_no>/<int:sem>")
@require_any(["admin", "hod", "faculty", "professor"])
def upload_marksheet(reg_no, sem):
    if sem < 1 or sem > 8:
        flash("Semester 1-8 only.", "err")
        return redirect(url_for("admin_dashboard"))
    f = request.files.get("marksheet")
    if not f or not f.filename:
        flash("No marksheet file selected.", "err")
        return redirect(url_for("admin_dashboard"))
    fn = secure_filename(f"{reg_no}_sem{sem}_{f.filename}")
    f.save(os.path.join(UPLOAD_MARKS, fn))
    uploaded_at = datetime.datetime.now().isoformat()
    Database.save_marksheet(reg_no, sem, fn, uploaded_at)
    flash(f"Semester {sem} marksheet uploaded.", "info")
    return redirect(url_for("admin_dashboard"))

# ---------- Student Portal ----------
@app.route("/student")
@require_any(["student"])
def student():
    reg = session.get("reg_no")
    s = Database.get_student_by_reg(reg)
    if not s:
        flash("Student record not found.", "err")
        return redirect(url_for("logout"))
    marks = Database.get_student_marksheets(reg)
    profs_list = Database.get_all_professors()
    profs = {p["email"]: p for p in profs_list}
    return render_template("student.html", s=s, marksheets=marks,
        timetable=TIMETABLE, periods=PERIODS, subjects=SUBJECTS, professors=profs)

# ---------- APIs ----------
@app.get("/api/students")
@require_any(["admin", "hod", "faculty", "professor"])
def api_students():
    cat = request.args.get("cat", "all")
    rows = Database.get_all_students()

    def get_cgpa(x):
        try: return float(x.get("cgpa") or 0.0)
        except: return 0.0
    def get_attn(x):
        try: return float(x.get("attendance") or 0.0)
        except: return 0.0

    if cat == "high_cgpa":
        rows.sort(key=lambda x: -get_cgpa(x))
    elif cat == "low_cgpa":
        rows.sort(key=lambda x: get_cgpa(x))
    elif cat == "high_attn":
        rows = [r for r in rows if get_attn(r) >= 90]
        rows.sort(key=lambda x: -get_attn(x))
    elif cat == "low_attn":
        rows = [r for r in rows if get_attn(r) < 75]
        rows.sort(key=lambda x: get_attn(x))
    elif cat == "hosteller":
        rows = [r for r in rows if "HOS" in (r.get("day_hos") or "").upper()]
    elif cat == "dayscholar":
        rows = [r for r in rows if "DAY" in (r.get("day_hos") or "").upper()]
    return jsonify(rows)

# ---------- Helpers ----------
def _stats(students):
    n = len(students)
    if not n:
        return {"total": 0, "avg_attn": 0, "avg_cgpa": 0, "shortage": 0}
    def get_attn(s):
        try: return float(s.get("attendance") or 0.0)
        except: return 0.0
    def get_cgpa(s):
        try: return float(s.get("cgpa") or 0.0)
        except: return 0.0
    avg_attn = round(sum(get_attn(s) for s in students) / n, 1)
    avg_cgpa = round(sum(get_cgpa(s) for s in students) / n, 2)
    shortage = sum(1 for s in students if get_attn(s) < 75)
    return {"total": n, "avg_attn": avg_attn, "avg_cgpa": avg_cgpa, "shortage": shortage}

def _todays_birthdays(students):
    today = datetime.date.today()
    out = []
    for s in students:
        dob = s.get("dob")
        if not dob:
            continue
        try:
            d = datetime.datetime.strptime(str(dob)[:10], "%Y-%m-%d").date()
            if d.month == today.month and d.day == today.day:
                msg = f"Wishing {s['name']} a very happy birthday from HIT Smart Academic! May you have an inspiring year ahead."
                s_copy = dict(s)
                s_copy["wa_link"] = f"https://wa.me/91{s.get('whatsapp')}?text={urllib.parse.quote(msg)}"
                out.append(s_copy)
        except:
            pass
    return out

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=5000)
