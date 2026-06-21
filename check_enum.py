from config import Config
from sqlalchemy import inspect, create_engine, text

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

with engine.connect() as conn:
    result = conn.execute(text("SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='users' AND COLUMN_NAME='role'"))
    column_type = result.fetchone()[0]
    print(f"Role column type: {column_type}")
