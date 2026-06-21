from config import Config
from sqlalchemy import inspect, create_engine

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
inspector = inspect(engine)

columns = inspector.get_columns('users')
for col in columns:
    print(f"{col['name']}: {col['type']} - Nullable: {col['nullable']}")
