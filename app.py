"""HIT CSE-A Batch Dashboard — Flask backend."""
import os, sqlite3, datetime, urllib.parse
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template, jsonify, send_from_directory, flash
from werkzeug.utils import secure_filename

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "students.db")
UPLOAD_PHOTOS = os.path.join(BASE, "static", "uploads", "photos")
UPLOAD_MARKS = os.path.join(BASE, "static", "uploads", "marksheets")
os.makedirs(UPLOAD_PHOTOS, exist_ok=True)
os.makedirs(UPLOAD_MARKS, exist_ok=True)

PROFESSOR_PASSWORD = "HIT2026"
PROF_EMAIL_DOMAIN = "@hit.edu.in"

app = Flask(__name__)
app.secret_key = "hit-cse-a-2025-secret"

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

# ---------- Timetable (from uploaded image) ----------
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
def require(role):
    def deco(fn):
        @wraps(fn)
        def wrap(*a, **k):
            if session.get("role") != role: return redirect(url_for("login"))
            return fn(*a, **k)
        return wrap
    return deco

# ---------- Routes ----------
@app.route("/")
def login():
    if session.get("role") == "student": return redirect(url_for("student"))
    if session.get("role") == "professor": return redirect(url_for("professor"))
    return render_template("login.html")

@app.post("/login")
def do_login():
    role = request.form.get("role")
    if role == "professor":
        email = request.form.get("email","").strip().lower()
        pwd = request.form.get("password","")
        if not email.endswith(PROF_EMAIL_DOMAIN):
            flash("Professor email must end with @hit.edu.in", "err"); return redirect(url_for("login"))
        if pwd != PROFESSOR_PASSWORD:
            flash("Invalid professor password.", "err"); return redirect(url_for("login"))
        con = db()
        prof = con.execute("SELECT * FROM professors WHERE email=?", (email,)).fetchone()
        if not prof:
            con.execute("INSERT INTO professors(email,name) VALUES(?,?)",(email, email.split("@")[0].title()))
            con.commit()
            prof = con.execute("SELECT * FROM professors WHERE email=?", (email,)).fetchone()
        con.close()
        session["role"]="professor"; session["email"]=email; session["name"]=prof["name"]
        return redirect(url_for("professor"))
    else:
        reg = request.form.get("reg_no","").strip()
        pwd = request.form.get("password","")
        con = db(); s = con.execute("SELECT * FROM students WHERE reg_no=?", (reg,)).fetchone(); con.close()
        if not s or s["password"] != pwd:
            flash("Invalid Reg No or Password.", "err"); return redirect(url_for("login"))
        session["role"]="student"; session["reg_no"]=reg; session["name"]=s["name"]
        return redirect(url_for("student"))

@app.route("/forgot")
def forgot():
    role = request.args.get("role","student")
    who = request.args.get("who","").strip()
    con = db()
    if role == "student":
        s = con.execute("SELECT * FROM students WHERE reg_no=?", (who,)).fetchone()
        if not s or not s["whatsapp"]:
            con.close(); flash("No WhatsApp number on record for that Reg No.", "err"); return redirect(url_for("login"))
        msg = f"Hello {s['name']}, your HIT dashboard password is: {s['password']}"
        wa = f"https://wa.me/91{s['whatsapp']}?text={urllib.parse.quote(msg)}"
        con.close(); return redirect(wa)
    else:
        con.close()
        flash(f"Professor password is fixed: {PROFESSOR_PASSWORD}", "info")
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

# ---------- Professor ----------
@app.route("/professor")
@require("professor")
def professor():
    con = db()
    students = [dict(r) for r in con.execute("SELECT * FROM students ORDER BY reg_no").fetchall()]
    profs = [dict(r) for r in con.execute("SELECT * FROM professors").fetchall()]
    marks = [dict(r) for r in con.execute("SELECT * FROM marksheets").fetchall()]
    con.close()
    stats = _stats(students)
    birthdays = _todays_birthdays(students)
    return render_template("professor.html",
        students=students, stats=stats, birthdays=birthdays,
        timetable=TIMETABLE, periods=PERIODS, subjects=SUBJECTS,
        professors=profs, marksheets=marks, me=session.get("name"))

@app.post("/professor/upload_photo/<reg_no>")
@require("professor")
def upload_photo(reg_no):
    f = request.files.get("photo")
    if not f: flash("No file.", "err"); return redirect(url_for("professor"))
    fn = secure_filename(f"{reg_no}_{f.filename}")
    f.save(os.path.join(UPLOAD_PHOTOS, fn))
    con = db(); con.execute("UPDATE students SET photo=? WHERE reg_no=?", (fn, reg_no)); con.commit(); con.close()
    flash("Photo uploaded.", "info"); return redirect(url_for("professor"))

@app.post("/professor/upload_marksheet/<reg_no>/<int:sem>")
@require("professor")
def upload_marksheet(reg_no, sem):
    if sem < 1 or sem > 8: flash("Semester 1-8 only.", "err"); return redirect(url_for("professor"))
    f = request.files.get("marksheet")
    if not f: flash("No file.", "err"); return redirect(url_for("professor"))
    fn = secure_filename(f"{reg_no}_sem{sem}_{f.filename}")
    f.save(os.path.join(UPLOAD_MARKS, fn))
    con = db()
    con.execute("INSERT OR REPLACE INTO marksheets(reg_no,semester,filename,uploaded_at) VALUES(?,?,?,?)",
                (reg_no, sem, fn, datetime.datetime.now().isoformat()))
    con.commit(); con.close()
    flash(f"Semester {sem} marksheet uploaded.", "info"); return redirect(url_for("professor"))

@app.post("/professor/upload_prof_photo")
@require("professor")
def upload_prof_photo():
    f = request.files.get("photo")
    if not f: return redirect(url_for("professor"))
    fn = secure_filename(f"prof_{session['email']}_{f.filename}")
    f.save(os.path.join(UPLOAD_PHOTOS, fn))
    con = db(); con.execute("UPDATE professors SET photo=? WHERE email=?", (fn, session["email"])); con.commit(); con.close()
    return redirect(url_for("professor"))

# ---------- Student ----------
@app.route("/student")
@require("student")
def student():
    reg = session["reg_no"]
    con = db()
    s = dict(con.execute("SELECT * FROM students WHERE reg_no=?", (reg,)).fetchone())
    marks = [dict(r) for r in con.execute("SELECT * FROM marksheets WHERE reg_no=? ORDER BY semester", (reg,)).fetchall()]
    profs = {p["email"]: dict(p) for p in con.execute("SELECT * FROM professors").fetchall()}
    con.close()
    return render_template("student.html", s=s, marksheets=marks,
        timetable=TIMETABLE, periods=PERIODS, subjects=SUBJECTS, professors=profs)

# ---------- API for filters ----------
@app.get("/api/students")
@require("professor")
def api_students():
    cat = request.args.get("cat","all")
    con = db()
    rows = [dict(r) for r in con.execute("SELECT * FROM students").fetchall()]
    con.close()
    if cat == "high_cgpa": rows.sort(key=lambda x:-x["cgpa"])
    elif cat == "low_cgpa": rows.sort(key=lambda x:x["cgpa"])
    elif cat == "high_attn": rows = [r for r in rows if r["attendance"]>=90]; rows.sort(key=lambda x:-x["attendance"])
    elif cat == "low_attn": rows = [r for r in rows if r["attendance"]<75]; rows.sort(key=lambda x:x["attendance"])
    elif cat == "hosteller": rows = [r for r in rows if "HOS" in (r["day_hos"] or "").upper()]
    elif cat == "dayscholar": rows = [r for r in rows if "DAY" in (r["day_hos"] or "").upper()]
    return jsonify(rows)

# ---------- Helpers ----------
def _stats(students):
    n = len(students)
    if not n: return {"total":0,"avg_attn":0,"avg_cgpa":0,"shortage":0}
    avg_attn = round(sum(s["attendance"] for s in students)/n, 1)
    avg_cgpa = round(sum(s["cgpa"] for s in students)/n, 2)
    shortage = sum(1 for s in students if s["attendance"] < 75)
    return {"total":n,"avg_attn":avg_attn,"avg_cgpa":avg_cgpa,"shortage":shortage}

def _todays_birthdays(students):
    today = datetime.date.today()
    out = []
    for s in students:
        if not s.get("dob"): continue
        try:
            d = datetime.datetime.strptime(s["dob"],"%Y-%m-%d").date()
            if d.month == today.month and d.day == today.day:
                msg = f"Wishing {s['name']} a very happy birthday from HIT CSE-A! May you have a wonderful year ahead."
                s = dict(s); s["wa_link"] = f"https://wa.me/91{s['whatsapp']}?text={urllib.parse.quote(msg)}"
                out.append(s)
        except: pass
    return out

if __name__ == "__main__":
    if not os.path.exists(DB):
        import seed; seed.main()
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=5000)
