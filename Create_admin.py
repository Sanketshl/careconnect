"""
Run once after fix_admin.sql to bcrypt-hash the admin password:
    python create_admin.py
"""
from app import create_app
from extensions import db, bcrypt
from models import Admin

app = create_app()
with app.app_context():
    admin = Admin.query.filter_by(email="admin@careconnect.com").first()
    if admin:
        admin.password = bcrypt.generate_password_hash("admin123").decode("utf-8")
        db.session.commit()
        print("✅ Done  →  admin@careconnect.com / admin123")
    else:
        db.session.add(Admin(
            name="Admin",
            email="admin@careconnect.com",
            password=bcrypt.generate_password_hash("admin123").decode("utf-8"),
        ))
        db.session.commit()
        print("✅ Admin created  →  admin@careconnect.com / admin123")