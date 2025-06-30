from sqlalchemy import create_engine, text
from .config import settings

# Database connection configuration
def create_db_engine():
    """
    Create a SQLAlchemy engine for the given database URL.
    
    :param db_url: Database connection URL
    :return: SQLAlchemy DB_ENGINE object
    """
    try:
        DB_ENGINE = create_engine(settings.PERSISTENCE_CONNECTION_URL)
    
        if settings.PERSISTENCE_CONNECTION_URL.startswith('sqlite:'):
            with DB_ENGINE.connect() as connection:
                connection.execute(text("SELECT 1"))
        
        return DB_ENGINE
    except Exception as e:
        settings.logger.error(f"Failed to create database engine: {str(e)}")