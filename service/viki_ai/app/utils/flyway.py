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
        print(f"Error: flyway.conf not found at {flyway_conf_path}")
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
        else:
            updated_lines.append(line + '\n' if line else '\n')
    
    # Write the updated content back to flyway.conf
    with open(flyway_conf_path, 'w') as file:
        file.writelines(updated_lines)
    
    print(f"Successfully updated flyway.conf at {flyway_conf_path}")
    print("Updated values:")
    print(f"  flyway.locations = {settings.FLYWAY_LOCATION}")
    print(f"  flyway.url = {settings.FLYWAY_URL}")
    print(f"  flyway.user = {settings.PERSISTENCE_USERNAME}")
    print(f"  flyway.password = {settings.PERSISTENCE_PASSWORD}")
    print(f"  flyway.baselineOnMigrate = {str(settings.FLYWAY_MIGRATION_BASELINE).lower()}")