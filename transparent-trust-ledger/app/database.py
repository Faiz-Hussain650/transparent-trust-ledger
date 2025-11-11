from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

print("✅ DATABASE_URL:", settings.DATABASE_URL)

engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
