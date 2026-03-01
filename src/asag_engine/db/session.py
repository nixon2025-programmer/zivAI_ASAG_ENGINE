from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from asag_engine.config import settings

DATABASE_URL = settings.database_url

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()