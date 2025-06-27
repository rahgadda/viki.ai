import pyfiglet
from .app.utils import flyway

def main():
    """
    Entry point for the VIKI AI.
    This is a FastAPI application that serves as a wrapper for the VIKI AI API.
    """
    
    # Print the welcome message
    print(pyfiglet.figlet_format("VIKI AI").rstrip())
    print("Welcome to VIKI.AI!!!\nThe AI Agent platform for intelligent actions. \n")

    flyway.update_flyway_config()

if __name__ == "__main__":
    main()