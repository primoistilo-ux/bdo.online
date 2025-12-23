import sqlite3
from werkzeug.security import generate_password_hash

db = sqlite3.connect("users.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    username TEXT UNIQUE,
    password TEXT,
    birthday TEXT,
    phone TEXT,
    profile_image TEXT
)
""")

hashed = generate_password_hash("123456")

cursor.execute(
    """
    INSERT OR IGNORE INTO users
    (email, username, password, birthday, phone, profile_image)
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        "admin@email.com",
        "admin",
        hashed,
        "2000-01-01",
        "09123456789",
        "default.png"
    )
)

db.commit()
db.close()

print("Database with profile image ready")
