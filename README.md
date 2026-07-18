# HIT CSE-A Batch Dashboard (2025–2029)

A full-stack **Flask + HTML/CSS/JavaScript** student & faculty dashboard for
**Hindusthan Institute of Technology, Coimbatore — CSE-A Batch (2025-2029)**.

Built from the class Excel spreadsheet (`students.xlsx`).

## Features

- **Login page** with two roles: **Student** (Reg No + password) and **Professor** (email + fixed password `HIT2026`)
- Professor accepts **any email ending with `@hit.edu.in`**
- Student **forgot password** → sends the password to the student's registered WhatsApp number via `wa.me` (opens WhatsApp with the message pre-filled)
- **Live clock** in the header (Asia/Kolkata locale via browser)
- **Themes**: Light, Dark, Royal (purple), Emerald (green), Sunset (orange) — with smooth transitions
- **Stats dashboard**: Total Strength, Average Attendance, Average CGPA, Shortage Attendance
- **Categorized sorting/filtering**: All / Hosteller / Dayscholar / Low Attendance / High Attendance / High CGPA / Low CGPA
- **Search** by name or Reg No
- **Student detail modal** with full information from the Excel
- **Photo upload** per student (professor side) — appears on the student's own dashboard too
- **Marksheet upload** for **all 8 semesters** per student — students automatically see their uploaded marksheets
- **Today's Timetable** modal built from your uploaded timetable image — click any subject code to see the **subject name, faculty photo, faculty name, weekly hours** and category
- **Birthday auto-wish**: on every professor login the app checks DOBs. Any student whose birthday is today shows a banner + a one-click WhatsApp link that opens WhatsApp with a pre-filled birthday message to their registered number.
- **Professor can upload their own photo** — it shows up in the subject info modal for both students and professors

## Run locally

```bash
# 1. Install
python -m pip install -r requirements.txt

# 2. Seed the database from the Excel (first run only)
python seed.py

# 3. Start the server
python app.py

# open http://localhost:5000
```

## Login credentials

**Professor** — any email like `senthilkumar@hit.edu.in` / password `HIT2026`

**Student** — Reg No (from Excel) / password = **last 6 digits of the Reg No**
- Example: `720825103001` / `103001`

## Notes

- WhatsApp messages open via `https://wa.me/91<number>?text=...` — free, no API keys required. If you later want fully-automatic sending, plug in Twilio's WhatsApp API in `app.py` at the `_todays_birthdays` helper.
- All uploads go to `static/uploads/photos/` and `static/uploads/marksheets/`.
- Database is a single `students.db` SQLite file next to `app.py`. Delete it and re-run `seed.py` to reset.
