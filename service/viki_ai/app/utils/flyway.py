import os
from .config import settings


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
        line = line.strip()
        if line.startswith('flyway.locations='):
            updated_lines.append(f'flyway.locations={settings.FLYWAY_LOCATION}\n')
        elif line.startswith('flyway.url='):
            updated_lines.append(f'flyway.url={settings.FLYWAY_URL}\n')
        elif line.startswith('flyway.user='):
            updated_lines.append(f'flyway.user={settings.PERSISTENCE_USERNAME}\n')
        elif line.startswith('flyway.password='):
            updated_lines.append(f'flyway.password={settings.PERSISTENCE_PASSWORD}\n')
        elif line.startswith('flyway.baselineOnMigrate='):
            updated_lines.append(f'flyway.baselineOnMigrate={str(settings.FLYWAY_MIGRATION_BASELINE).lower()}\n')
    
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