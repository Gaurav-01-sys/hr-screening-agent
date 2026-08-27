import os
import tempfile
import platform
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Streamlit Cloud mounts code in a read-only filesystem at /mount/src/...
# We must use the /tmp directory (or gettempdir) for the SQLite DB when deployed.
if platform.system() == "Linux" and "mount/src" in os.path.abspath(__file__):
    db_path = os.path.join(tempfile.gettempdir(), "hr_screening.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./hr_screening.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_database_schema() -> None:
    """Create tables and add the small set of backward-compatible columns.

    The starter project uses SQLite without a migration runner. Keeping these
    additive migrations here prevents an existing local/deployed database from
    rejecting the richer candidate and rubric fields.
    """
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name != "sqlite":
        return

    additions = {
        "candidates": {
            "email": "VARCHAR",
            "phone": "VARCHAR",
            "location": "VARCHAR",
            "current_title": "VARCHAR",
            "current_company": "VARCHAR",
            "domains": "JSON",
            "certifications": "JSON",
            "work_authorization": "VARCHAR",
            "notice_period_days": "INTEGER",
            "red_flags": "JSON",
        },
        "candidate_experiences": {"domains": "JSON"},
        "jobs": {
            "location": "VARCHAR",
            "work_authorization_required": "VARCHAR",
            "max_notice_period_days": "INTEGER",
            "red_flags": "JSON",
        },
        "rules": {"max_days": "INTEGER"},
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in additions.items():
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, column_type in columns.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {column_type}'))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
