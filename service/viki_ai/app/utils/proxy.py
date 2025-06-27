from math import log
import os
from .config import settings

def log_proxy_config():
    """
    Log the current proxy configuration.
    """
    
    settings.logger.debug("Current proxy configuration:")
    settings.logger.debug(f"  HTTP_PROXY = {os.environ.get('HTTP_PROXY', '') or os.environ.get('http_proxy', '')}")
    settings.logger.debug(f"  HTTPS_PROXY = {os.environ.get('HTTPS_PROXY', '') or os.environ.get('https_proxy', '')}")
    settings.logger.debug(f"  NO_PROXY = {os.environ.get('NO_PROXY', '') or os.environ.get('no_proxy', '')}")

def update_proxy_config():
    """
    Update proxy configuration based on environment variables.
    """
    
    # Set the proxy environment variables if they are defined
    if settings.HTTPPROXY:
        os.environ['HTTP_PROXY'] = settings.HTTPPROXY
        os.environ['http_proxy'] = settings.HTTPPROXY
    if settings.HTTPSPROXY:
        os.environ['HTTPS_PROXY'] = settings.HTTPSPROXY
        os.environ['https_proxy'] = settings.HTTPSPROXY
    if settings.NOPROXY:
        os.environ['NO_PROXY'] = settings.NOPROXY
        os.environ['no_proxy'] = settings.NOPROXY
    
    log_proxy_config()
    
def delete_proxy_config():
    """
    Delete proxy configuration by clearing environment variables.
    """
    
    # Clear the proxy environment variables
    os.environ.pop('HTTP_PROXY', None)
    os.environ.pop('HTTPS_PROXY', None)
    os.environ.pop('NO_PROXY', None)
    os.environ.pop('http_proxy', None)
    os.environ.pop('https_proxy', None)
    os.environ.pop('no_proxy', None)

    log_proxy_config()