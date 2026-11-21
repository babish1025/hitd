"""Database adapter supporting Supabase PostgreSQL with SQLite fallback."""
import os
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))

DB_FILE = os.path.join(BASE, "students.db")

class PGResultWrapper:
    def __init__(self, cursor):
        self.cursor = cursor

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

class PGConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        # Convert ? to %s for PostgreSQL
        pg_sql = sql.replace("?", "%s")
        
        # Handle SQLite-specific INSERT OR REPLACE for marksheets
        if "INSERT OR REPLACE INTO marksheets" in pg_sql:
            pg_sql = """
            INSERT INTO marksheets (reg_no, semester, filename, uploaded_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (reg_no, semester)
            DO UPDATE SET filename = EXCLUDED.filename, uploaded_at = EXCLUDED.uploaded_at
            """
        
        from psycopg2.extras import RealDictCursor
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        if params is not None:
            cur.execute(pg_sql, params)
        else:
            cur.execute(pg_sql)
        return PGResultWrapper(cur)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db():
    """Returns a database connection to Supabase PostgreSQL, or fallback to SQLite."""
    use_supabase = os.getenv("USE_SUPABASE", "1") == "1"
    
    if use_supabase:
        try:
            import psycopg2
            host = os.getenv("DB_HOST", "")
            port = int(os.getenv("DB_PORT", "5432"))
            user = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASSWORD", "")
            dbname = os.getenv("DB_NAME", "postgres")
            
            raw_conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=dbname,
                sslmode="require",
                connect_timeout=5
            )
            return PGConnectionWrapper(raw_conn)
        except Exception as e:
            print(f"[DB Warning] Could not connect to Supabase PostgreSQL: {e}. Falling back to SQLite.")

    # SQLite fallback
    import sqlite3
    c = sqlite3.connect(DB_FILE)
    c.row_factory = sqlite3.Row
    return c

