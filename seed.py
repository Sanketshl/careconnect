from extensions import db, bcrypt
from models import Admin

def run_seed(app):
    with app.app_context():
        admin = Admin.query.filter_by(email="admin@careconnect.com").first()
        if not admin:
            hashed = bcrypt.generate_password_hash("admin123").decode("utf-8")
            db.session.add(Admin(
                name="Admin",
                email="admin@careconnect.com",
                password=hashed,
            ))
            db.session.commit()
            print("✅ Admin created  →  admin@careconnect.com / admin123")
        else:
            # If plain-text from SQL seed, hash it now
            if not admin.password.startswith("$2"):
                admin.password = bcrypt.generate_password_hash("admin123").decode("utf-8")
                db.session.commit()
                print("✅ Admin password hashed  →  admin@careconnect.com / admin123")
            else:
                print("ℹ️  Admin already exists, skipping seed.")