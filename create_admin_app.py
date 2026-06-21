from app import app, db, bcrypt
from models import Admin

with app.app_context():
    # Check if admin exists
    existing_admin = Admin.query.filter_by(email="admin@care.com").first()
    if existing_admin:
        print("Admin already exists. Deleting and recreating...")
        db.session.delete(existing_admin)
        db.session.commit()

    # Create new admin
    hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
    new_admin = Admin(name="Admin", email="admin@care.com", password=hashed_password)
    db.session.add(new_admin)
    db.session.commit()

    print("✅ Admin created successfully!")
    print("   Email: admin@care.com")
    print("   Password: admin123")