import sqlite3

def add_grace_60_column():
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()

    # Check if column already exists
    c.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in c.fetchall()]
    
    if "grace_60" not in columns:
        c.execute("ALTER TABLE jobs ADD COLUMN grace_60 TEXT")
        print("✅ 'grace_60' column added to 'jobs' table.")
    else:
        print("ℹ️ 'grace_60' column already exists.")

    conn.commit()
    conn.close()

# Run the update
add_grace_60_column()
