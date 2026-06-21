"""
Run this ONCE after importing careconnect_schema.sql:
    python create_admin.py

This bcrypt-hashes the admin password so login works correctly.
Credentials:  admin@careconnect.com / admin123
"""
from app import create_app
from extensions import db, bcrypt
from models import Admin

app = create_app()

with app.app_context():
    admin = Admin.query.filter_by(email="admin@careconnect.com").first()
    hashed = bcrypt.generate_password_hash("admin123").decode("utf-8")

    if admin:
        admin.password = hashed
        db.session.commit()
        print("✅ Admin password hashed  →  admin@careconnect.com / admin123")
    else:
        db.session.add(Admin(
            name     = "Admin",
            email    = "admin@careconnect.com",
            password = hashed,
        ))
        db.session.commit()
        print("✅ Admin created  →  admin@careconnect.com / admin123")