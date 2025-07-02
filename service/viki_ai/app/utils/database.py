from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base   
from .config import settings


DB_ENGINE = None
SessionLocal = None
# Initialize Base immediately so models can use it during import
Base = declarative_base()

# Database connection configuration
def create_db_engine():
    """
    Create a SQLAlchemy engine for the given database URL.
    
    :param db_url: Database connection URL
    :return: SQLAlchemy DB_ENGINE object
    """
    try:

        global DB_ENGINE, SessionLocal

        if DB_ENGINE is not None:
            return DB_ENGINE
    
        DB_ENGINE = create_engine(settings.PERSISTENCE_CONNECTION_URL)

        if settings.PERSISTENCE_CONNECTION_URL.startswith('sqlite:'):
            with DB_ENGINE.connect() as connection:
                connection.execute(text("SELECT 1"))

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=DB_ENGINE)
        return DB_ENGINE
    except Exception as e:
        settings.logger.error(f"Failed to create database engine: {str(e)}")


def get_db():
    """
    Dependency function to get database session for FastAPI endpoints
    """
    global SessionLocal
    if SessionLocal is None:
        create_db_engine()  # Ensure engine is created
    
    if SessionLocal is None:
        raise RuntimeError("Database session not initialized")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()