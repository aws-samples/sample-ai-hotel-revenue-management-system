import json
import time
import logging
from functools import wraps
from flask import request, redirect, url_for, session, current_app, jsonify
from urllib.parse import quote

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler if it doesn't exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def token_required(f):
    """
    Decorator to require a valid token for API endpoints
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if authentication is disabled for local development
        if current_app.config.get('DISABLE_AUTH', False):
            logger.info("Authentication is disabled for local development")
            # Add a mock user to the session for development ONLY in local development
            if 'user' not in session:
                session['user'] = {
                    'sub': 'local-development-user',
                    'email': 'dev@example.com',
                    'name': 'Local Developer',
                    'given_name': 'Local',
                    'family_name': 'Developer'
                }
            return f(*args, **kwargs)
        
        # Check if user is in session
        if 'user' in session:
            logger.info(f"User found in session: {session.get('user', {}).get('email')}")
            # Check if token is still valid
            if 'token_expiration' in session:
                if session['token_expiration'] > time.time():
                    logger.info("Token is still valid")
                    return f(*args, **kwargs)
                else:
                    logger.info("Token has expired")
            else:
                # No expiration set, assume token is valid only if we have user info
                if session.get('user', {}).get('sub') and session.get('user', {}).get('email'):
                    logger.info("No token expiration found, but user info exists")
                    return f(*args, **kwargs)
                else:
                    logger.info("No token expiration and incomplete user info")
                return f(*args, **kwargs)
        else:
            logger.info("No user found in session")
        
        # Token expired or not found, clear session
        session.pop('user', None)
        session.pop('id_token', None)
        session.pop('access_token', None)
        session.pop('token_expiration', None)
        token = None
        
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Check cookies
        if not token and 'id_token' in request.cookies:
            token = request.cookies.get('id_token')
        
        # Check session
        if not token and 'id_token' in session:
            token = session['id_token']
        
        # If no token, redirect to login
        if not token:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
            else:
                return redirect(url_for('auth.login', next=quote(request.url)))
        
        # In a real application, we would verify the token here
        # For local development, we'll just accept any token
        
        return f(*args, **kwargs)
    
    return decorated

def get_cognito_login_url(redirect_uri):
    """
    Get the Cognito login URL
    
    Args:
        redirect_uri (str): Redirect URI after login
        
    Returns:
        str: Cognito login URL
    """
    # Check if Cognito is configured
    logger.info(f"COGNITO_DOMAIN: {current_app.config.get('COGNITO_DOMAIN')}")
    logger.info(f"COGNITO_CLIENT_ID: {current_app.config.get('COGNITO_CLIENT_ID')}")
    logger.info(f"COGNITO_APP_CLIENT_ID: {current_app.config.get('COGNITO_APP_CLIENT_ID')}")
    logger.info(f"DISABLE_AUTH: {current_app.config.get('DISABLE_AUTH')}")
    
    # Try to get client ID from either COGNITO_CLIENT_ID or COGNITO_APP_CLIENT_ID
    client_id = current_app.config.get('COGNITO_CLIENT_ID') or current_app.config.get('COGNITO_APP_CLIENT_ID')
    
    if not current_app.config.get('COGNITO_DOMAIN') or not client_id:
        logger.warning("Cognito is not configured properly")
        return url_for('auth.login')
    
    # Build the Cognito login URL
    cognito_domain = current_app.config['COGNITO_DOMAIN']
    
    # Ensure the domain has the correct format
    if not cognito_domain.startswith('http'):
        cognito_domain = f"https://{cognito_domain}"
    
    # URL encode the redirect URI
    import urllib.parse
    encoded_redirect_uri = urllib.parse.quote(redirect_uri)
    
    # Build the login URL
    login_url = (
        f"{cognito_domain}/login?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"scope=email+openid+profile&"
        f"redirect_uri={encoded_redirect_uri}"
    )
    
    logger.info(f"Generated Cognito login URL: {login_url}")
    return login_url

def get_cognito_logout_url(redirect_uri):
    """
    Get the Cognito logout URL
    
    Args:
        redirect_uri (str): Redirect URI after logout
        
    Returns:
        str: Cognito logout URL
    """
    # Try to get client ID from either COGNITO_CLIENT_ID or COGNITO_APP_CLIENT_ID
    client_id = current_app.config.get('COGNITO_CLIENT_ID') or current_app.config.get('COGNITO_APP_CLIENT_ID')
    
    # Check if Cognito is configured
    if not current_app.config.get('COGNITO_DOMAIN') or not client_id:
        logger.warning("Cognito is not configured properly")
        return url_for('main.index')
    
    # Build the Cognito logout URL
    cognito_domain = current_app.config['COGNITO_DOMAIN']
    
    # Ensure the domain has the correct format
    if not cognito_domain.startswith('http'):
        cognito_domain = f"https://{cognito_domain}"
    
    # Build the logout URL
    logout_url = (
        f"{cognito_domain}/logout?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}"
    )
    
    logger.info(f"Generated Cognito logout URL: {logout_url}")
    return logout_url
