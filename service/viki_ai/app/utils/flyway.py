import os
import subprocess
import sys

from .config import settings
from .database import create_db_engine

def create_sqlite_db():
    """
    Create SQLite database if it does not exist.
    """
    db_path = settings.PERSISTENCE_CONNECTION_URL.replace('sqlite:///', '')

    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Check if the database file already exists
    if not os.path.exists(db_path):
        try:
            create_db_engine()
            settings.logger.debug(f"SQLite database created at {db_path}")
        except Exception as e:
            settings.logger.error(f"Failed to create SQLite database: {e}")
    else:
        settings.logger.debug(f"SQLite database already exists at {db_path}")


def run_flyway_migrations():
    """
    Run Flyway migrations to ensure the database schema is up-to-date.
    """
    try:
        current_dir = os.getcwd()
        
        # Change to the flyway folder
        os.chdir(settings.FLYWAY_FOLDER_LOCATION)
        
        # Run flyway migrate
        result = subprocess.run(
            ["flyway", "migrate"],
            capture_output=True,
            text=True,
            check=True
        )
        
        settings.logger.debug("Flyway migrations completed successfully.")
        settings.logger.debug(f"Flyway output: {result.stdout}")
        
    except subprocess.CalledProcessError as e:
        settings.logger.error(f"Flyway command failed: {e}")
        settings.logger.error(f"Flyway stderr: {e.stderr}")
        settings.logger.error(f"Flyway stdout: {e.stdout}")
    except FileNotFoundError as e:
        settings.logger.error(f"Flyway executable not found. Make sure Flyway is installed and in PATH: {e}")
    except Exception as e:
        settings.logger.error(f"Failed to run Flyway migrations: {e}")
    finally:
        # Always return to the original directory
        os.chdir(current_dir)

def update_flyway_config():
    """
    Update flyway.conf file with values from settings
    """
    # Get the current working directory, move one level above and navigate to db folder
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)  # Move up to project root/
    flyway_conf_path = os.path.join(parent_dir, 'db', 'flyway.conf')
    
    # Check if flyway.conf exists
    if not os.path.exists(flyway_conf_path):
        settings.logger.error(f"Error: flyway.conf not found at {flyway_conf_path}")
        return False
    
    # Read the current flyway.conf content
    with open(flyway_conf_path, 'r') as file:
        lines = file.readlines()
    
    # Update the configuration values
    updated_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('flyway.locations='):
            updated_lines.append(f'flyway.locations={settings.FLYWAY_LOCATION}\n')
        elif stripped_line.startswith('flyway.url='):
            updated_lines.append(f'flyway.url={settings.FLYWAY_URL}\n')
        elif stripped_line.startswith('flyway.user='):
            updated_lines.append(f'flyway.user={settings.PERSISTENCE_USERNAME}\n')
        elif stripped_line.startswith('flyway.password='):
            updated_lines.append(f'flyway.password={settings.PERSISTENCE_PASSWORD}\n')
        elif stripped_line.startswith('flyway.baselineOnMigrate='):
            updated_lines.append(f'flyway.baselineOnMigrate={str(settings.FLYWAY_MIGRATION_BASELINE).lower()}\n')
        else:
            # Keep the original line for non-matching patterns
            updated_lines.append(line)
    
    # Write the updated content back to flyway.conf
    with open(flyway_conf_path, 'w') as file:
        file.writelines(updated_lines)

    settings.logger.debug(f"Successfully updated flyway.conf at {flyway_conf_path}")
    settings.logger.debug("Updated values:")
    settings.logger.debug(f"  flyway.locations = {settings.FLYWAY_LOCATION}")
    settings.logger.debug(f"  flyway.url = {settings.FLYWAY_URL}")
    settings.logger.debug(f"  flyway.user = {settings.PERSISTENCE_USERNAME}")
    settings.logger.debug(f"  flyway.password = {settings.PERSISTENCE_PASSWORD}")
    settings.logger.debug(f"  flyway.baselineOnMigrate = {str(settings.FLYWAY_MIGRATION_BASELINE).lower()}")