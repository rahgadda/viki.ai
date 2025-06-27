import pyfiglet
from .app.utils.config import settings
from .app.utils import flyway
from .app.utils import proxy

def main():
    """
    Entry point for the VIKI AI.
    This is a FastAPI application that serves as a wrapper for the VIKI AI API.
    """

    # Print the welcome message
    print(pyfiglet.figlet_format("VIKI AI").rstrip())
    print("The AI Agent platform for intelligent actions!\n")

    # Update proxy configuration
    proxy.update_proxy_config()

    # Create DB
    flyway.update_flyway_config()

if __name__ == "__main__":
    main()