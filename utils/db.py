import sqlite3
import hashlib
from datetime import datetime

def make_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_table():
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password, role, email):
    hashed_password = make_hash(password)
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
              (username, hashed_password, role, email))
    conn.commit()
    conn.close()


def init_db():
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            location TEXT,
            visa_sponsorship TEXT,
            urgency TEXT,
            posted_by TEXT,
            timestamp TEXT,
            remote TEXT,
            salary_range TEXT
        )
    ''')
    conn.commit()
    conn.close()

def init_applications_db():
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            candidate_username TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_job(title, description, location, visa_sponsorship, urgency, posted_by, remote, salary_range):
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    c.execute('''
        INSERT INTO jobs (title, description, location, visa_sponsorship, urgency, posted_by, timestamp, remote, salary_range)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, location, visa_sponsorship, urgency, posted_by, timestamp, remote, salary_range))
    conn.commit()
    conn.close()

def get_jobs():
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY timestamp DESC")
    jobs = c.fetchall()
    conn.close()
    return jobs

def get_applications_for_recruiter(job_id):
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("""
        SELECT candidate_username, message, resume, first_name, last_name, email, phone
        FROM applications
        WHERE job_id = ?
    """, (job_id,))
    results = c.fetchall()
    conn.close()
    return results



def get_applications_by_candidate(candidate_username):
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("""
        SELECT jobs.id, jobs.title, jobs.description, jobs.location,
               jobs.visa_sponsorship, jobs.urgency, jobs.posted_by,
               jobs.timestamp, jobs.remote, jobs.salary_range,
               applications.message
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.candidate_username = ?
        ORDER BY jobs.timestamp DESC
    """, (candidate_username,))
    results = c.fetchall()
    conn.close()
    return results



def get_user_by_username(username):
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("SELECT username, password, role, email FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user


def get_jobs_by_user(username):
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE posted_by = ?", (username,))
    jobs = c.fetchall()
    conn.close()
    return jobs

def get_skills_for_job(job_id):
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("""
        SELECT name FROM skills
        JOIN job_skills ON skills.id = job_skills.skill_id
        WHERE job_skills.job_id = ?
    """, (job_id,))
    result = [row[0] for row in c.fetchall()]
    conn.close()
    return ", ".join(result)

def filter_jobs(skill=None, location=None, remote=None, visa=None, urgency=None, title=None):
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()

    query = """
        SELECT DISTINCT jobs.*
        FROM jobs
        LEFT JOIN job_skills ON jobs.id = job_skills.job_id
        LEFT JOIN skills ON job_skills.skill_id = skills.id
        WHERE 1 = 1
    """
    params = []

    if skill and skill != "All":
        query += " AND skills.name = ?"
        params.append(skill)
    if location:
        query += " AND jobs.location LIKE ?"
        params.append(f"%{location}%")
    if remote and remote != "All":
        query += " AND jobs.remote = ?"
        params.append(remote)
    if visa and visa != "All":
        query += " AND jobs.visa_sponsorship = ?"
        params.append(visa)
    if urgency and urgency != "All":
        query += " AND jobs.urgency = ?"
        params.append(urgency)
    if title:
        query += " AND jobs.title LIKE ?"
        params.append(f"%{title}%")

    query += " ORDER BY jobs.timestamp DESC"

    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    return results


def get_all_skills():
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT name FROM skills ORDER BY name")
    skills = [row[0] for row in c.fetchall()]
    conn.close()
    return skills

def apply_to_job(job_id, candidate_username, message, resume, first, last, email, phone):
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO applications 
        (job_id, candidate_username, message, resume, first_name, last_name, email, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (job_id, candidate_username, message, resume, first, last, email, phone))
    conn.commit()
    conn.close()

def get_email_by_username(username):
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None