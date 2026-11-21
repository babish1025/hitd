# HIT CSE-A Batch Dashboard (2025–2029)

A full-stack **Flask + Supabase Cloud PostgreSQL** student & faculty dashboard for
**Hindusthan Institute of Technology, Coimbatore — CSE-A Batch (2025-2029)**.

Built from the class Excel spreadsheet (`students.xlsx`).

## Features

- **Supabase Cloud Database Integration** (`ap-northeast-2` region) with local SQLite fallback
- **Login page** with two roles: **Student** (Reg No + password) and **Professor** (email + fixed password `HIT2026`)
- Professor accepts **any email ending with `@hit.edu.in`**
- Student **forgot password** → sends the password to the student's registered WhatsApp number via `wa.me`
- **Live clock** in the header (Asia/Kolkata locale via browser)
- **Themes**: Light, Dark, Royal (purple), Emerald (green), Sunset (orange)
- **Stats dashboard**: Total Strength, Average Attendance, Average CGPA, Shortage Attendance
- **Categorized sorting/filtering**: All / Hosteller / Dayscholar / Low Attendance / High Attendance / High CGPA / Low CGPA
- **Search** by name or Reg No
- **Student detail modal** with full information from the Excel (contact, parent details, address, etc.)
- **Photo upload** per student (faculty side) — appears on the student's own dashboard
- **Marksheet upload** for **all 8 semesters** per student — students automatically see their uploaded marksheets
- **Today's Timetable** modal — click any subject code to see the **subject name, faculty photo, faculty name, weekly hours** and category
- **Birthday auto-wish**: checks DOBs with a one-click WhatsApp link
- **Professor profile photo upload**

## Supabase Configuration (.env)

The application connects to Supabase Cloud PostgreSQL:
- **Region**: `ap-northeast-2`
- **Project URL**: `https://xtaszaaplwkuworidmhd.supabase.co`
- **Tables**: `students` (63 records seeded), `professors` (7 records seeded), `marksheets`

## Run locally

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Seed database to Supabase (if needed)
python seed_supabase.py

# 3. Start the server
python app.py

# Open http://localhost:5000
```

## Login credentials

**Professor** — any email like `senthilkumar@hit.edu.in` / password `HIT2026`

**Student** — Reg No (from Excel) / password = **last 6 digits of the Reg No**
- Example: `720825103001` / `103001`
