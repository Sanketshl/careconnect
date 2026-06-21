"""
fix_ids.py  —  Fixes user IDs so they stay consistent (1, 2, 3)
              and re-hashes passwords correctly.

Run ONCE after any database reset:
  cd D:\project2\backend
  .venv\Scripts\activate
  python fix_ids.py
  python app.py
  
Then clear browser localStorage and log in fresh.
"""
import sys
import pymysql

HOST = "127.0.0.1"
USER = "root"
PASS = "Adarsh"
DB   = "careconnect"

USERS = [
    {"id":1, "name":"Admin", "email":"admin@care.com",  "password":"admin123", "role":"admin",     "phone":"9999999999","location":"City Center"},
    {"id":2, "name":"Rahul", "email":"rahul@gmail.com", "password":"1234",     "role":"elderly",   "phone":"8888888888","location":"Delhi"},
    {"id":3, "name":"Amit",  "email":"amit@gmail.com",  "password":"1234",     "role":"volunteer", "phone":"7777777777","location":"Mumbai"},
]

try:
    from flask import Flask
    from flask_bcrypt import Bcrypt
except ImportError:
    print("❌ Flask not found. Activate venv first.")
    sys.exit(1)

_app = Flask(__name__)
_app.config["JWT_SECRET_KEY"] = "fix"
bcrypt = Bcrypt(_app)

print("\n🔧 CareConnect — Fix User IDs")
print("=" * 44)

try:
    conn = pymysql.connect(host=HOST, user=USER, password=PASS,
                           database=DB, charset="utf8mb4")
    cur = conn.cursor()

    # Disable FK checks so we can delete freely
    cur.execute("SET FOREIGN_KEY_CHECKS=0")

    # Delete seed users by email
    cur.execute("DELETE FROM users WHERE email IN ('admin@care.com','rahul@gmail.com','amit@gmail.com')")
    print("🗑️  Deleted old seed users")

    # Re-insert with fixed IDs
    for u in USERS:
        with _app.app_context():
            hashed = bcrypt.generate_password_hash(u["password"]).decode("utf-8")
        cur.execute(
            "INSERT INTO users (id, name, email, password, role, phone, location) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (u["id"], u["name"], u["email"], hashed,
             u["role"], u["phone"], u["location"])
        )
        print("✅ Created id={} {} / {} [{}]".format(
              u["id"], u["email"], u["password"], u["role"]))

        if u["role"] == "volunteer":
            cur.execute("INSERT IGNORE INTO volunteers (user_id) VALUES (%s)", (u["id"],))

    # Re-enable FK checks
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()
    cur.close()
    conn.close()

    print("\n" + "=" * 44)
    print("✅ Fixed! User IDs are now permanent:")
    print("   ID 1 → admin@care.com   / admin123")
    print("   ID 2 → rahul@gmail.com  / 1234")
    print("   ID 3 → amit@gmail.com   / 1234")
    print()
    print("Now:")
    print("  1. Restart Flask:  python app.py")
    print("  2. Open browser console and run:  localStorage.clear()")
    print("  3. Log in fresh")
    print("=" * 44 + "\n")

except Exception as ex:
    import traceback
    print("❌ Error:", ex)
    traceback.print_exc()