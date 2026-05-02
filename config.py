import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")  # Required: Set this in your environment
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")  # Required: Set this in your environment
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # Enhanced database connection pool settings to prevent connection loss
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "pool_size": 20,
        "max_overflow": 20,
        "pool_timeout": 30,
        "connect_args": {
            "connect_timeout": 10,
            "read_timeout": 30,
            "write_timeout": 30,
            "charset": "utf8mb4",
            "sql_mode": "STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION",
        }
    }

    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "noreply@example.com"))
