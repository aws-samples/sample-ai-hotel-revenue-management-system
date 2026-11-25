import time
import logging
from functools import wraps
from urllib.parse import urlencode, urlsplit
from flask import request, redirect, url_for, session, current_app, jsonify
from app.auth.tokens import TokenVerificationError, verify_id_token

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

def establish_session(claims):
    """Sign the user in from the claims of a verified Cognito ID token, and from nothing else."""
    session.clear()
    session.permanent = True
    session['user'] = {
        'sub': claims['sub'],
        'email': claims.get('email', ''),
        'email_verified': claims.get('email_verified') in (True, 'true'),
        'name': claims.get('name') or claims.get('email') or 'User',
        'given_name': claims.get('given_name', ''),
        'family_name': claims.get('family_name', '')
    }
    session['token_expiration'] = int(claims['exp'])

def safe_redirect_target(target):
    """Return target if it is a path on this site (for example /history), otherwise the index URL."""
    fallback = url_for('main.index')
    if not target or not isinstance(target, str):
        return fallback
    # Browsers treat a backslash like a slash and drop tabs and newlines inside URLs
    if '\\' in target or any(ord(ch) < 0x20 or ord(ch) == 0x7f for ch in target):
        return fallback
    # Only a single leading slash: "//host" and "https://host" lead to another site
    if not target.startswith('/') or target.startswith('//'):
        return fallback
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return fallback
    return target

def _relative_request_url():
    """The current path and query string, for the next parameter of the login page."""
    query = request.query_string.decode('utf-8', 'replace')
    return f"{request.path}?{query}" if query else request.path

def _clear_identity():
    for key in ('user', 'token_expiration', 'id_token', 'access_token'):
        session.pop(key, None)

def token_required(f):
    """
    Decorator that serves the view only to a user whose identity the server has verified.

    The identity comes from the session, which the server sets only after verifying a Cognito ID token
    (code exchange in /auth/callback, or /auth/process-token), or from an Authorization: Bearer ID token
    that passes the same verification (app.auth.tokens.verify_id_token).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if authentication is disabled for local development
        if current_app.config.get('DISABLE_AUTH', False):
            logger.debug("Authentication is disabled for local development")
            # Add a mock user to the session for development ONLY in local development
            if 'user' not in session:
                session['user'] = {
                    'sub': 'local-development-user',
                    'email': 'dev@example.com',
                    'email_verified': False,
                    'name': 'Local Developer',
                    'given_name': 'Local',
                    'family_name': 'Developer'
                }
            return f(*args, **kwargs)
        
        # A session the server set after verifying a token, and that has not expired
        user = session.get('user') or {}
        expires_at = session.get('token_expiration')
        if user.get('sub') and isinstance(expires_at, (int, float)) and expires_at > time.time():
            return f(*args, **kwargs)

        # Not signed in, or the sign-in expired: drop whatever identity the session still holds
        _clear_identity()

        # An API client may present a Cognito ID token instead; it must pass full verification
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                claims = verify_id_token(auth_header[len('Bearer '):].strip())
            except TokenVerificationError as exc:
                logger.warning(f"Rejected bearer token: {exc}")
                return jsonify({'error': 'Unauthorized', 'message': 'Invalid token'}), 401
            establish_session(claims)
            return f(*args, **kwargs)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
        return redirect(url_for('auth.login', next=_relative_request_url()))
    
    return decorated

def cognito_base_url():
    """The Cognito domain as an https URL, or None if it is not configured."""
    cognito_domain = (current_app.config.get('COGNITO_DOMAIN') or '').rstrip('/')
    if not cognito_domain:
        return None
    if not cognito_domain.startswith('http'):
        cognito_domain = f"https://{cognito_domain}"
    return cognito_domain

def get_cognito_login_url(redirect_uri, state, code_challenge):
    """
    Get the Cognito authorize URL for the authorization code grant with PKCE
    
    Args:
        redirect_uri (str): Redirect URI after login
        state (str): Random value that the callback must receive back unchanged
        code_challenge (str): S256 PKCE challenge of the verifier kept in the session
        
    Returns:
        str: Cognito login URL
    """
    # Try to get client ID from either COGNITO_CLIENT_ID or COGNITO_APP_CLIENT_ID
    client_id = current_app.config.get('COGNITO_CLIENT_ID') or current_app.config.get('COGNITO_APP_CLIENT_ID')
    cognito_domain = cognito_base_url()
    
    if not cognito_domain or not client_id:
        logger.warning("Cognito is not configured properly")
        return url_for('auth.login')
    
    query = urlencode({
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'email openid profile',
        'redirect_uri': redirect_uri,
        'state': state,
        'code_challenge_method': 'S256',
        'code_challenge': code_challenge
    })
    return f"{cognito_domain}/oauth2/authorize?{query}"

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
    cognito_domain = cognito_base_url()
    if not cognito_domain or not client_id:
        logger.warning("Cognito is not configured properly")
        return url_for('main.index')
    
    # Build the logout URL
    logout_url = (
        f"{cognito_domain}/logout?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}"
    )
    
    logger.info(f"Generated Cognito logout URL: {logout_url}")
    return logout_url
