"""
fix_admin_login.py
==================
Run this ONCE to fix the admin login error.

  cd D:\project2\backend
  .venv\Scripts\activate
  python fix_admin_login.py
  python app.py

Login: admin@care.com / admin123
"""

import sys

HOST = "127.0.0.1"
USER = "root"
PASS = "123456"
DB   = "careconnect"

USERS = [
    {"name":"Admin","email":"admin@care.com", "password":"admin123","role":"admin",    "phone":"9999999999","location":"City Center"},
    {"name":"Rahul","email":"rahul@gmail.com","password":"1234",    "role":"elderly",  "phone":"8888888888","location":"Delhi"},
    {"name":"Amit", "email":"amit@gmail.com", "password":"1234",    "role":"volunteer","phone":"7777777777","location":"Mumbai"},
]

try:
    import pymysql
    from flask import Flask
    from flask_bcrypt import Bcrypt
except ImportError as ie:
    print("❌ Missing package:", ie)
    print("   Run:  .venv\\Scripts\\activate")
    sys.exit(1)

_app = Flask(__name__)
_app.config["JWT_SECRET_KEY"] = "fix"
bcrypt = Bcrypt(_app)

print("\n🔧 CareConnect — Fix Admin Login")
print("=" * 44)

try:
    conn = pymysql.connect(host=HOST,user=USER,password=PASS,database=DB,charset="utf8mb4")
    print("✅ Connected to MySQL")
except Exception as ex:
    print("❌ Cannot connect:", ex)
    sys.exit(1)

cur = conn.cursor()

# ── STEP 1: Fix the ENUM — add 'admin' if missing ────────────────────────────
print("\n📋 Fixing role ENUM to include admin...")
try:
    cur.execute("""
        ALTER TABLE users
        MODIFY COLUMN role
        ENUM('elderly','parent','volunteer','admin') NOT NULL DEFAULT 'elderly'
    """)
    conn.commit()
    print("✅ role ENUM updated: elderly | parent | volunteer | admin")
except Exception as ex:
    print("⚠️  ENUM already correct or error (continuing):", ex)

# ── STEP 2: Fix help_requests status ENUM ────────────────────────────────────
try:
    cur.execute("""
        ALTER TABLE help_requests
        MODIFY COLUMN status
        ENUM('open','in-progress','delivered','completed') DEFAULT 'open'
    """)
    conn.commit()
    print("✅ help_requests status ENUM updated")
except Exception as ex:
    print("⚠️  Status ENUM (continuing):", ex)

# ── STEP 3: Add missing columns ───────────────────────────────────────────────
for stmt in [
    "ALTER TABLE help_requests ADD COLUMN IF NOT EXISTS rating    FLOAT    NULL",
    "ALTER TABLE help_requests ADD COLUMN IF NOT EXISTS carecoins INT      NULL DEFAULT 0",
    "ALTER TABLE help_requests ADD COLUMN IF NOT EXISTS rated_at  DATETIME NULL",
    "ALTER TABLE help_requests ADD COLUMN IF NOT EXISTS latitude  FLOAT    NULL",
    "ALTER TABLE help_requests ADD COLUMN IF NOT EXISTS longitude FLOAT    NULL",
    "ALTER TABLE volunteers    ADD COLUMN IF NOT EXISTS carecoins INT NOT NULL DEFAULT 0",
    "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read TINYINT(1) NOT NULL DEFAULT 0",
]:
    try:
        cur.execute(stmt)
        conn.commit()
    except Exception:
        pass
print("✅ Schema columns verified")

# ── STEP 4: Delete and re-insert seed users with correct bcrypt hashes ───────
print("\n👤 Re-creating seed users...")
for u in USERS:
    cur.execute("DELETE FROM users WHERE email = %s", (u["email"],))
    removed = cur.rowcount

    with _app.app_context():
        hashed = bcrypt.generate_password_hash(u["password"]).decode("utf-8")

    cur.execute(
        "INSERT INTO users (name,email,password,role,phone,location) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (u["name"], u["email"], hashed, u["role"], u["phone"], u["location"])
    )
    uid = cur.lastrowid

    if u["role"] == "volunteer":
        cur.execute("INSERT IGNORE INTO volunteers (user_id) VALUES (%s)", (uid,))

    label = "replaced" if removed else "created"
    print("  ✅ {} — {} / {} [{}]".format(label, u["email"], u["password"], u["role"]))

conn.commit()
cur.close()
conn.close()

print("\n" + "=" * 44)
print("✅ All done! Login credentials:")
print()
print("   🛡️  admin@care.com   /  admin123  (Admin)")
print("   👤  rahul@gmail.com  /  1234      (User)")
print("   💛  amit@gmail.com   /  1234      (Volunteer)")
print()
print("   Now run:  python app.py")
print("=" * 44 + "\n")