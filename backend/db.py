from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL with fallback to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./job_search.db")

# Handle different database URL formats
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False})
elif DATABASE_URL.startswith("https://"):
    # Convert Supabase HTTPS URL to PostgreSQL connection string
    # This is a fallback - you should use the proper PostgreSQL connection string
    raise ValueError("Please use a PostgreSQL connection string instead of HTTPS URL. Check your DATABASE_URL environment variable.")
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()