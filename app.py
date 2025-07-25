import streamlit as st
from utils.db import (
    init_db, init_applications_db, create_user_table, add_user,
    get_user_by_username, make_hash, add_job, get_jobs, apply_to_job,
    get_jobs_by_user, get_applications_for_recruiter, get_applications_by_candidate,
    get_skills_for_job, get_all_skills, filter_jobs, get_email_by_username
)
from utils.email_utils import send_recruiter_notification
import sqlite3
import os
from datetime import datetime

# Initialize database tables
init_db()
init_applications_db()
create_user_table()

st.set_page_config(page_title="60day.com", layout="centered", initial_sidebar_state="collapsed")

# Global dark theme visibility fix
st.markdown("""
    <style>
    .st-expanderContent {
        background-color: #1e1e1e !important;
        color: #f0f0f0 !important;
    }
    .job-card, .stMarkdown {
        color: #f0f0f0 !important;
    }
    .stMarkdown p {
        color: #f0f0f0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "username" not in st.session_state:
    st.session_state["username"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

# ---------- AUTH SCREENS (Login / Signup) ----------

def show_login():
    st.title("🔐 Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit and username and password:
            user_record = get_user_by_username(username)
            if user_record:
                stored_hashed_pw, role = user_record[1], user_record[2]
                if make_hash(password) == stored_hashed_pw:
                    st.session_state.username = username
                    st.session_state.user_role = role
                    st.success(f"✅ Logged in as {username} ({role})")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("Username not found.")

def show_signup():
    st.title("📝 Sign Up")
    with st.form("signup_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        email = st.text_input("Email Address")
        role = st.radio("Register as:", ["recruiter", "candidate"])
        submit = st.form_submit_button("Create Account")

        if submit and username and password and email:
            try:
                add_user(username, password, role, email)
                st.success("✅ Account created! Please log in.")
            except Exception as e:
                st.error(f"Error: {e}")

# ---------- DASHBOARD SCREENS ----------

def show_recruiter_post_form():
    st.header("📢 Post a Job")
    with st.form("job_form"):
        title = st.text_input("Job Title")
        description = st.text_area("Description")
        location = st.text_input("Location")
        visa = st.selectbox("Visa Sponsorship", ["Yes", "No"])
        urgency = st.selectbox("Urgency", ["Immediate", "Within 30 Days", "Flexible"])
        remote = st.selectbox("Remote Option", ["Yes", "No"])
        salary = st.text_input("Salary Range (e.g. 90K–110K)")
        skills = st.text_input("Key Skills (comma-separated)")
        post = st.form_submit_button("Post Job")

        if post and title and description and location and salary:
            conn = sqlite3.connect("data/jobs.db")
            c = conn.cursor()
            c.execute('''
                INSERT INTO jobs (title, description, location, visa_sponsorship, urgency, posted_by, timestamp, remote, salary_range, skills)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?)
            ''', (title, description, location, visa, urgency, st.session_state.username, remote, salary, skills))
            conn.commit()
            conn.close()
            st.success("✅ Job posted!")

def show_recruiter_jobs():
    st.header("📄 Your Posted Jobs")
    jobs = get_jobs_by_user(st.session_state.username)
    for job in jobs:
        with st.expander(f"🔹 {job[1]}"):
            st.markdown(f"""
            **Job Title:** {job[1]}  
            **Description:** {job[2]}  
            **Location:** {job[3]}  
            **Visa Sponsorship:** {job[4]}  
            **Urgency:** {job[5]}  
            **Posted By:** {job[6]}  
            **Remote Option:** {job[8]}  
            **Salary Range:** {job[9]}  
            **Skills:** {get_skills_for_job(job[0]) or 'N/A'}
            """)

def show_recruiter_applications():
    st.header("📥 Applications Received")
    jobs = get_jobs_by_user(st.session_state.username)
    for job in jobs:
        applications = get_applications_for_recruiter(job[0])
        if applications:
            st.subheader(f"📨 Applicants for: {job[1]} (Job ID {job[0]})")
            for app in applications:
                candidate, message, resume, first, last, email, phone = app
                st.markdown(f"""
                - **Name:** {first} {last}  
                  **Username:** {candidate}  
                  **Email:** {email}  
                  **Phone:** {phone}  
                  **Message:** {message}
                """)
                if resume:
                    resume_path = f"temp_resume_{job[0]}_{candidate}.pdf"
                    with open(resume_path, "wb") as f:
                        f.write(resume)
                    with open(resume_path, "rb") as f:
                        st.download_button("📄 Download Resume", data=f, file_name=f"resume_{candidate}.pdf")

def show_candidate_jobs():
    st.header("💼 Available Jobs")

    applied_job_ids = {app[0] for app in get_applications_by_candidate(st.session_state.username)}

    with st.expander("🔍 Filter Jobs"):
        title = st.text_input("Job Title")
        skills = get_all_skills()
        selected_skill = st.selectbox("Skill", ["All"] + skills)
        location = st.text_input("Location")
        remote = st.selectbox("Remote Option", ["All", "Yes", "No"])
        visa = st.selectbox("Visa Sponsorship", ["All", "Yes", "No"])
        urgency = st.selectbox("Urgency", ["All", "Immediate", "Within 30 Days", "Flexible"])
        search = st.button("Apply Filters")

    if search:
        jobs = filter_jobs(
            skill=selected_skill,
            location=location,
            remote=remote,
            visa=visa,
            urgency=urgency,
            title=title
        )
    else:
        jobs = get_jobs()

    jobs = [job for job in jobs if job[0] not in applied_job_ids]

    for job in jobs:
        with st.expander(f"🔹 {job[1]}"):
            st.markdown(f"""
            **Job Title:** {job[1]}  
            **Description:** {job[2]}  
            **Visa Sponsorship:** {job[4]}  
            **Urgency:** {job[5]}  
            **Location:** {job[3]}  
            **Posted By:** {job[6]}  
            **Remote Option:** {job[8]}  
            **Salary Range:** {job[9]}  
            **Skills:** {get_skills_for_job(job[0]) or 'N/A'}
            """)
            if st.button(f"Apply for {job[1]}", key=f"applybtn_{job[0]}"):
                with st.form(f"apply_form_{job[0]}"):
                    st.markdown("### 📝 Application Form")
                    first = st.text_input("First Name")
                    last = st.text_input("Last Name")
                    email = st.text_input("Email")
                    phone = st.text_input("Mobile Number (with country code)")
                    resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
                    message = st.text_area("Message to recruiter")
                    submitted = st.form_submit_button("Submit Application")
                    if submitted:
                        resume_bytes = resume.read() if resume else None
                        apply_to_job(job[0], st.session_state.username, message, resume_bytes, first, last, email, phone)

                        recruiter_email = get_email_by_username(job[6])
                        candidate_name = f"{first} {last}"
                        send_recruiter_notification(
                            recruiter_email,
                            job_title=job[1],
                            candidate_name=candidate_name,
                            message=message,
                            resume_bytes=resume_bytes,
                            resume_filename=resume.name if resume else "resume.pdf"
                        )

                        st.success("✅ Application submitted!")
                        st.rerun()

def show_candidate_applications():
    st.header("📋 Jobs You Applied To")
    apps = get_applications_by_candidate(st.session_state.username)
    for app in apps:
        st.markdown(f"""
        **Job Title:** {app[1]}  
        **Description:** {app[2]}  
        **Location:** {app[3]}  
        **Visa Sponsorship:** {app[4]}  
        **Urgency:** {app[5]}  
        **Posted By:** {app[6]}  
        **Remote Option:** {app[8]}  
        **Salary Range:** {app[9]}  
        **Your Message:** {app[10]}
        """)

# ---------- APP FLOW ----------

def logout():
    st.session_state.username = None
    st.session_state.user_role = None
    st.success("✅ Logged out successfully!")
    st.rerun()

if not st.session_state.username:
    st.markdown("<h1 style='text-align:center'>👋 Welcome to 60day.com</h1>", unsafe_allow_html=True)
    mode = st.radio("Select an option:", ["🔐 Login", "📝 Sign Up"], horizontal=True)
    if mode == "🔐 Login":
        show_login()
    else:
        show_signup()
else:
    role = st.session_state.user_role
    st.sidebar.success(f"Logged in as {st.session_state.username} ({role})")
    if st.sidebar.button("🚪 Logout"):
        logout()

    if role == "recruiter":
        choice = st.sidebar.radio("Recruiter Menu", ["📢 Post Job", "📄 View Jobs Posted", "📥 Applications Received"])
        if choice == "📢 Post Job":
            show_recruiter_post_form()
        elif choice == "📄 View Jobs Posted":
            show_recruiter_jobs()
        else:
            show_recruiter_applications()
    else:
        choice = st.sidebar.radio("Candidate Menu", ["Job Board", "My Applications"])
        if choice == "Job Board":
            show_candidate_jobs()
        else:
            show_candidate_applications()
