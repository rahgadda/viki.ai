from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base   
from .config import settings


DB_ENGINE = None
SessionLocal = None
Base = None

# Database connection configuration
def create_db_engine():
    """
    Create a SQLAlchemy engine for the given database URL.
    
    :param db_url: Database connection URL
    :return: SQLAlchemy DB_ENGINE object
    """
    try:

        global DB_ENGINE, SessionLocal, Base

        if DB_ENGINE is not None:
            return DB_ENGINE
    
        DB_ENGINE = create_engine(settings.PERSISTENCE_CONNECTION_URL)

        if settings.PERSISTENCE_CONNECTION_URL.startswith('sqlite:'):
            with DB_ENGINE.connect() as connection:
                connection.execute(text("SELECT 1"))

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=DB_ENGINE)
        Base = declarative_base()
        return DB_ENGINE
    except Exception as e:
        settings.logger.error(f"Failed to create database engine: {str(e)}")