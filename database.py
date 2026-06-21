from extensions import db
from sqlalchemy import text


def connect_db(app):
    """
    Test the database connection on startup.
    db.init_app(app) must be called before this.
    """
    try:
        with app.app_context():
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        print("[OK] Connected to careconnect database successfully")
    except Exception as e:
        print("[ERROR] Database connection failed")
        print("   Error:", e)
        raise   # Re-raise so the app fails fast instead of silently