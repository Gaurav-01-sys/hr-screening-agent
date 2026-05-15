import os
import tempfile
import platform
from sqlalchemy import create_engine
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
