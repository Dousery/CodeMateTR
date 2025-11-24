"""Configuration utility functions for Flask app setup."""
import os


def configure_session(app, is_production=False):
    """
    Configure Flask session settings.
    
    Args:
        app: Flask application instance
        is_production (bool): Whether running in production mode
    """
    base_config = {
        'SESSION_COOKIE_PATH': '/',
        'SESSION_COOKIE_DOMAIN': None,
        'SESSION_REFRESH_EACH_REQUEST': False,
        'SESSION_TYPE': 'filesystem'
    }
    
    if is_production:
        production_config = {
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'None',
            'PERMANENT_SESSION_LIFETIME': 86400,  # 24 hours
            'SESSION_COOKIE_MAX_AGE': 86400,
            'SESSION_FILE_DIR': '/tmp/flask_session',
            'SESSION_FILE_THRESHOLD': 500
        }
        config = {**base_config, **production_config}
    else:
        dev_config = {
            'SESSION_COOKIE_SECURE': False,
            'SESSION_COOKIE_HTTPONLY': False,
            'SESSION_COOKIE_SAMESITE': 'None',
            'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour
            'SESSION_COOKIE_MAX_AGE': 3600
        }
        config = {**base_config, **dev_config}
    
    for key, value in config.items():
        app.config[key] = value


def get_cors_config(is_production=False):
    """
    Get CORS configuration based on environment.
    
    Args:
        is_production (bool): Whether running in production mode
        
    Returns:
        dict: CORS configuration dictionary
    """
    base_config = {
        'supports_credentials': True,
        'methods': ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        'allow_headers': [
            "Content-Type", 
            "Authorization", 
            "X-Requested-With", 
            "Origin", 
            "Accept", 
            "Access-Control-Allow-Origin"
        ],
        'expose_headers': [
            "Content-Type", 
            "Authorization", 
            "Access-Control-Allow-Origin"
        ]
    }
    
    if is_production:
        production_origins = [
            'https://codematetr.onrender.com',
            'https://btk-project-frontend.onrender.com'
        ]
        return {**base_config, 'origins': production_origins}
    else:
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        dev_origins = [
            frontend_url,
            'http://localhost:3000',
            'http://127.0.0.1:5173'
        ]
        return {**base_config, 'origins': dev_origins}


def is_production_environment():
    """
    Check if running in production environment.
    
    Returns:
        bool: True if in production, False otherwise
    """
    return os.getenv('FLASK_ENV') == 'production'
