import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Debugging Configuration
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Proxy Details
    HTTPPROXY: str = os.getenv("HTTPPROXY", "")
    HTTPSPROXY: str = os.getenv("HTTPSPROXY", "")
    NOPROXY: str = os.getenv("NOPROXY", "")

    # Flyway location
    FLYWAY_LOCATION: str = os.getenv("FLYWAY_LOCATION", "")
    FLYWAY_URL: str = os.getenv("FLYWAY_URL", "")

    # Persistence Configuration
    PERSISTENCE_TYPE: str = os.getenv("PERSISTENCE_TYPE", "SQLLITE")
    PERSISTENCE_CONNECTION_URL: str = os.getenv("PERSISTENCE_CONNECTION_URL", "")
    PERSISTENCE_USERNAME: str = os.getenv("PERSISTENCE_USERNAME", "")
    PERSISTENCE_PASSWORD: str = os.getenv("PERSISTENCE_PASSWORD", "")
    PERSISTENCE_DB_LOCATION: str = os.getenv("PERSISTENCE_DB_LOCATION", "")
    PERSISTENCE_MIGRATION_BASELINE: bool = os.getenv("PERSISTENCE_MIGRATION_BASELINE", "True").lower() == "true"
    PERSISTENCE_POOL_SIZE: int = int(os.getenv("PERSISTENCE_POOL_SIZE", "10"))
    PERSISTENCE_MAX_OVERFLOW: int = int(os.getenv("PERSISTENCE_MAX_OVERFLOW", "20"))

settings = Settings()