import sqlite3

def login_user(role, username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    table = "candidates" if role == "Candidate" else "recruiters"
    cursor.execute(f"SELECT * FROM {table} WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def signup_user(role, username, password, extra_info):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    table = "candidates" if role == "Candidate" else "recruiters"
    cursor.execute(f"INSERT INTO {table} (username, password, extra_info) VALUES (?, ?, ?)", 
                   (username, password, extra_info))
    conn.commit()
    conn.close()