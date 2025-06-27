import os
from dotenv import load_dotenv
from . import logs 

load_dotenv()

class Settings:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Prevent re-initialization
        if Settings._initialized:
            return
        Settings._initialized = True
        
        # Debugging Configuration
        self.DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

        # Logger Configuration
        self.logger = logs.setup_logging(self.DEBUG)

        # Proxy Details
        self.HTTPPROXY: str = os.getenv("HTTPPROXY", "")
        self.HTTPSPROXY: str = os.getenv("HTTPSPROXY", "")
        self.NOPROXY: str = os.getenv("NOPROXY", "")

        # Flyway location
        self.FLYWAY_LOCATION: str = os.getenv("FLYWAY_LOCATION", "")
        self.FLYWAY_URL: str = os.getenv("FLYWAY_URL", "")
        self.FLYWAY_MIGRATION_BASELINE: bool = os.getenv("FLYWAY_MIGRATION_BASELINE", "True").lower() == "true"

        # Persistence Configuration
        self.PERSISTENCE_TYPE: str = os.getenv("PERSISTENCE_TYPE", "SQLLITE")
        self.PERSISTENCE_CONNECTION_URL: str = os.getenv("PERSISTENCE_CONNECTION_URL", "")
        self.PERSISTENCE_USERNAME: str = os.getenv("PERSISTENCE_USERNAME", "")
        self.PERSISTENCE_PASSWORD: str = os.getenv("PERSISTENCE_PASSWORD", "")
        self.PERSISTENCE_POOL_SIZE: int = int(os.getenv("PERSISTENCE_POOL_SIZE", "10"))
        self.PERSISTENCE_MAX_OVERFLOW: int = int(os.getenv("PERSISTENCE_MAX_OVERFLOW", "20"))

def get_settings() -> Settings:
    """Get the singleton settings instance."""
    return Settings()

# Global instance - this will be the same object every time
settings = Settings()