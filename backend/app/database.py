from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import config
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = config(
    'DATABASE_URL',
    default='postgresql://clausewise_user:clausewise_secure_password@localhost:5432/clausewise'
)

# Create engine with security configurations
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,  # Set to True for SQL debugging
    connect_args={
        "sslmode": "prefer",
        "application_name": "clausewise_api"
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()