import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    
    # AWS Configuration
    AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
    
    # AgentCore Configuration
    AGENTCORE_RUNTIME_ARN = os.environ.get('AGENTCORE_RUNTIME_ARN', 'arn:aws:bedrock-agentcore:us-west-2:943562114123:runtime/hotel_revenue_optimization-2OYNqEGtl3')
    AGENTCORE_ENDPOINT = os.environ.get('AGENTCORE_ENDPOINT', '')
    
    # Timeout Configuration
    AGENTCORE_TIMEOUT = int(os.environ.get('AGENTCORE_TIMEOUT', '120'))  # 2 minutes
    AWS_CONNECT_TIMEOUT = int(os.environ.get('AWS_CONNECT_TIMEOUT', '10'))  # 10 seconds
    AWS_READ_TIMEOUT = int(os.environ.get('AWS_READ_TIMEOUT', '120'))  # 2 minutes
    
    # Cognito Configuration
    COGNITO_REGION = os.environ.get('COGNITO_REGION', AWS_REGION)
    COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', '')
    COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_APP_CLIENT_ID', '')
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
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Ensure these are set in production
    def __init__(self):
        assert os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production') != 'dev-key-please-change-in-production', \
            'SECRET_KEY must be set in production'
        assert os.environ.get('COGNITO_USER_POOL_ID'), 'COGNITO_USER_POOL_ID must be set in production'
        assert os.environ.get('COGNITO_APP_CLIENT_ID'), 'COGNITO_APP_CLIENT_ID must be set in production'
    
    # Disable authentication only if explicitly set
    DISABLE_AUTH = os.environ.get('DISABLE_AUTH', 'False').lower() == 'true'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
