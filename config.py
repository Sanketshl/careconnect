import os

# ── Do NOT use dotenv — hardcode defaults that always work ────────────────────
# Change these values to match YOUR MySQL setup

MYSQL_USER     = os.environ.get("DB_USER",     "root")
MYSQL_PASSWORD = os.environ.get("DB_PASSWORD", "123456")
MYSQL_HOST     = os.environ.get("DB_HOST",     "127.0.0.1")
MYSQL_DATABASE = os.environ.get("DB_NAME",     "careconnect")

class Config:
    SECRET_KEY     = "careconnect-secret-key-2025"
    JWT_SECRET_KEY = "careconnect-jwt-secret-2025"
    JWT_ACCESS_TOKEN_EXPIRES  = 86400      # 24 hours
    JWT_REFRESH_TOKEN_EXPIRES = 86400 * 7  # 7 days

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://{user}:{pw}@{host}/{db}".format(
            user = MYSQL_USER,
            pw   = MYSQL_PASSWORD,
            host = MYSQL_HOST,
            db   = MYSQL_DATABASE,
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False