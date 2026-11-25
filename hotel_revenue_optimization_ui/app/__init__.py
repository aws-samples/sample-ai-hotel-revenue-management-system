import os
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from app.config import config, production_config_errors
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

def create_app(config_name=None, config_overrides=None):
    """Create the Flask application.

    config_overrides (optional) is applied on top of the selected configuration; tests use it.
    """
    # Create and configure the app
    logger.info("Creating Flask application")
    app = Flask(__name__, instance_relative_config=True)
    
    # Load the configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    if config_overrides:
        app.config.update(config_overrides)

    # Refuse to start in production with a missing or guessable SECRET_KEY (it signs the session
    # cookie that holds the signed-in identity) or without the settings authentication relies on
    if config_name == 'production':
        problems = production_config_errors(app.config)
        if problems:
            raise RuntimeError('Refusing to start with an unsafe production configuration: ' + '; '.join(problems))
        if app.config.get('DISABLE_AUTH'):
            logger.warning("DISABLE_AUTH is set in production: every visitor is signed in as a local test user")
    
    # Add template filters
    # nosemgrep: useless-inner-function
    @app.template_filter('format_datetime')
    def format_datetime(value):
        """Format ISO datetime string for display with timezone"""
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                # Convert to Eastern Time for display
                from zoneinfo import ZoneInfo
                et = dt.astimezone(ZoneInfo('America/New_York'))
                return et.strftime('%Y-%m-%d %H:%M %Z')
            except:
                try:
                    # Fallback for simple datetime strings
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    return dt.strftime('%Y-%m-%d %H:%M EST')
                except:
                    return value
        return value
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Configure session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'hotel_rev_opt:'
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Register health blueprint
    from app.health import health_bp
    app.register_blueprint(health_bp)
    
    return app
