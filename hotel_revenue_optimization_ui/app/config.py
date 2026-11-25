import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Values that must never sign production session cookies: the development default, the placeholder in
# .env.example, and the suffix of the key that earlier versions of ecs.yaml derived from public values
WEAK_SECRET_KEYS = {'dev-key-please-change-in-production', 'your-secret-key-here'}
WEAK_SECRET_KEY_SUFFIX = '-production-key-2025'
MIN_SECRET_KEY_LENGTH = 32

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    
    # AWS Configuration
    AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
    
    # AgentCore Configuration: the ARN of your own runtime. There is no default; the app reports a clear
    # error when it is missing (production refuses to start).
    AGENTCORE_RUNTIME_ARN = os.environ.get('AGENTCORE_RUNTIME_ARN', '')
    AGENTCORE_ENDPOINT = os.environ.get('AGENTCORE_ENDPOINT', '')
    
    # Timeout Configuration
    # A report takes about 70 to 270 seconds depending on MODEL_PROVIDER; allow 6 minutes
    AGENTCORE_TIMEOUT = int(os.environ.get('AGENTCORE_TIMEOUT', '360'))
    AWS_CONNECT_TIMEOUT = int(os.environ.get('AWS_CONNECT_TIMEOUT', '10'))  # 10 seconds
    AWS_READ_TIMEOUT = int(os.environ.get('AWS_READ_TIMEOUT', '360'))  # the agent answers when the report is done
    
    # Cognito Configuration
    COGNITO_REGION = os.environ.get('COGNITO_REGION', AWS_REGION)
    COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', '')
    COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_APP_CLIENT_ID', '')
    COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID', '')
    COGNITO_CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET', '')
    COGNITO_DOMAIN = os.environ.get('COGNITO_DOMAIN', '')
    AUTH_REDIRECT_URI = os.environ.get('AUTH_REDIRECT_URI', '')
    
    # CloudFront Configuration
    CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', '')
    
    # Security Configuration
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', None)  # Set to CloudFront domain in production
    SESSION_COOKIE_NAME = 'hotel_rev_opt_session'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600  # 1 hour
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Content Security Policy
    CONTENT_SECURITY_POLICY = {
        'default-src': ["'self'"],
        'script-src': ["'self'", 'cdn.jsdelivr.net', "'unsafe-inline'"],
        'style-src': ["'self'", 'cdn.jsdelivr.net', "'unsafe-inline'"],
        'img-src': ["'self'", 'data:'],
        'font-src': ["'self'", 'cdn.jsdelivr.net'],
        'connect-src': ["'self'"]
    }

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Disable authentication for local development
    DISABLE_AUTH = os.environ.get('DISABLE_AUTH', 'True').lower() == 'true'

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    
    # Disable authentication for testing
    DISABLE_AUTH = True

class ProductionConfig(Config):
    """Production configuration.

    app.config.from_object() reads class attributes and never instantiates this class, so the
    production requirements are checked by production_config_errors(), which create_app() calls.
    """
    DEBUG = False
    TESTING = False
    
    # Disable authentication only if explicitly set
    DISABLE_AUTH = os.environ.get('DISABLE_AUTH', 'False').lower() == 'true'

def production_config_errors(app_config):
    """Return what makes a production configuration unsafe to start with (an empty list if nothing)."""
    errors = []
    secret_key = app_config.get('SECRET_KEY')
    if isinstance(secret_key, bytes):
        secret_key = secret_key.decode('utf-8', 'replace')
    if (not isinstance(secret_key, str) or len(secret_key) < MIN_SECRET_KEY_LENGTH
            or secret_key in WEAK_SECRET_KEYS or secret_key.endswith(WEAK_SECRET_KEY_SUFFIX)):
        errors.append(f'SECRET_KEY must be a random value of at least {MIN_SECRET_KEY_LENGTH} characters '
                      '(the ECS template injects one from AWS Secrets Manager)')
    if not app_config.get('DISABLE_AUTH'):
        for key in ('COGNITO_USER_POOL_ID', 'COGNITO_DOMAIN'):
            if not app_config.get(key):
                errors.append(f'{key} must be set')
        if not (app_config.get('COGNITO_APP_CLIENT_ID') or app_config.get('COGNITO_CLIENT_ID')):
            errors.append('COGNITO_APP_CLIENT_ID must be set')
    if not app_config.get('AGENTCORE_RUNTIME_ARN'):
        errors.append('AGENTCORE_RUNTIME_ARN must be set to the ARN of your Amazon Bedrock AgentCore runtime')
    return errors

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
