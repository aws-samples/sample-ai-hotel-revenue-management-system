from flask import render_template, redirect, url_for, request, session, current_app, jsonify
from app.auth import bp
from app.auth.cognito import (get_cognito_login_url, get_cognito_logout_url, cognito_base_url,
                              establish_session, safe_redirect_target)
from app.auth.tokens import TokenVerificationError, verify_id_token
import base64
import hashlib
import hmac
import logging
import secrets
import time
import requests

# Seconds to wait for the Cognito token endpoint
TOKEN_REQUEST_TIMEOUT = 10

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

def _redirect_uri():
    """The OAuth redirect URI. The authorize request and the token request must send the same value."""
    if current_app.config.get('AUTH_REDIRECT_URI'):
        # Use the configured redirect URI
        return current_app.config.get('AUTH_REDIRECT_URI')
    if current_app.config.get('CLOUDFRONT_DOMAIN'):
        # Use CloudFront domain for production
        return f"https://{current_app.config['CLOUDFRONT_DOMAIN']}/auth/callback"
    # Use local domain for development
    return url_for('auth.callback', _external=True)

def _pkce_challenge(code_verifier):
    """S256 code challenge (RFC 7636): base64url of the SHA-256 of the verifier, without padding."""
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')

def _auth_error(description, status):
    return render_template('auth/error.html', error="Authentication Error",
                           error_description=description), status

@bp.route('/login')
def login():
    """Login page"""
    next_url = safe_redirect_target(request.args.get('next'))

    # Check if authentication is disabled for local development
    if current_app.config.get('DISABLE_AUTH', False):
        logger.info("Authentication is disabled for local development")
        # Add a mock user to the session for development
        session['user'] = {
            'sub': 'local-development-user',
            'email': 'dev@example.com',
            'email_verified': False,
            'name': 'Local Developer'
        }
        return redirect(next_url)
    
    # Check if user is already logged in
    if session.get('user') and (session.get('token_expiration') or 0) > time.time():
        return redirect(next_url)
    
    # A fresh random state and PKCE verifier for every sign-in, kept in the signed session cookie.
    # The callback accepts an authorization code only together with this state, and redeems it with
    # this verifier, so a code started in another browser cannot sign this browser in.
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    session['oauth_state'] = state
    session['pkce_verifier'] = code_verifier
    session['post_login_next'] = next_url
    
    # Get the Cognito login URL
    login_url = get_cognito_login_url(_redirect_uri(), state=state, code_challenge=_pkce_challenge(code_verifier))
    
    return render_template('auth/login.html', login_url=login_url)

@bp.route('/callback')
def callback():
    """Callback endpoint for Cognito authentication"""
    # The state and verifier are single use, whatever the outcome
    expected_state = session.pop('oauth_state', None)
    code_verifier = session.pop('pkce_verifier', None)
    next_url = safe_redirect_target(session.pop('post_login_next', None))

    # If there's an error parameter, log it
    error = request.args.get('error')
    if error:
        logger.error(f"Error in Cognito callback: {error}")
        return render_template('auth/error.html', error=error, error_description=request.args.get('error_description'))

    code = request.args.get('code')
    if not code:
        # The Cognito app client allows only the authorization code flow (cognito.yaml AllowedOAuthFlows). A
        # callback without a code is not a sign-in this browser started, so tokens in it are never accepted:
        # signing in from a token in the URL would let anyone sign a victim into the sender's account.
        logger.warning("Rejected a sign-in callback without an authorization code")
        return _auth_error("The sign-in response is missing its authorization code. Please sign in again.", 400)

    received_state = request.args.get('state') or ''
    if not expected_state or not code_verifier or not hmac.compare_digest(
            received_state.encode('utf-8'), expected_state.encode('utf-8')):
        logger.warning("Rejected an authorization code whose state does not match this browser's sign-in")
        return _auth_error("The sign-in request could not be verified. Please sign in again.", 400)

    # Exchange the code for tokens
    client_id = current_app.config.get('COGNITO_CLIENT_ID') or current_app.config.get('COGNITO_APP_CLIENT_ID')
    client_secret = current_app.config.get('COGNITO_CLIENT_SECRET')
    cognito_domain = cognito_base_url()
    if not cognito_domain or not client_id:
        logger.error("Cognito is not configured properly")
        return _auth_error("Sign-in is not configured. Please contact support.", 500)

    token_request = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': _redirect_uri(),
        'code_verifier': code_verifier
    }
    if client_secret:
        # Confidential app client: requests sends client_id:client_secret as HTTP Basic authentication
        client_auth = (client_id, client_secret)
    else:
        # Public app client without a secret: PKCE alone binds the code to this browser
        client_auth = None
        token_request['client_id'] = client_id

    try:
        token_response = requests.post(
            f"{cognito_domain}/oauth2/token",
            data=token_request,
            auth=client_auth,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=TOKEN_REQUEST_TIMEOUT
        )
    except requests.RequestException as e:
        logger.error(f"Token request to Cognito failed: {e.__class__.__name__}")
        return _auth_error("An unexpected error occurred during authentication. Please try again or contact support.", 502)

    try:
        tokens = token_response.json()
    except ValueError:
        tokens = {}
    if not isinstance(tokens, dict):
        tokens = {}
    if token_response.status_code != 200:
        # Log the OAuth error code only (for example invalid_grant), never the request
        logger.error(f"Error exchanging code for tokens: HTTP {token_response.status_code} {tokens.get('error', '')}")
        return _auth_error("Failed to authenticate with Cognito. Please sign in again.", 401)

    # The ID token arrives over TLS from Cognito, but it is still verified before it is trusted
    try:
        claims = verify_id_token(tokens.get('id_token'))
    except TokenVerificationError as e:
        logger.error(f"Rejected the ID token from the Cognito token endpoint: {e}")
        return _auth_error("Failed to verify the sign-in. Please try again or contact support.", 401)

    establish_session(claims)
    logger.info(f"User signed in: sub={claims['sub']}")
    return redirect(next_url)

@bp.route('/logout')
def logout():
    """Logout endpoint"""
    # Clear the session
    session.clear()
    
    # Check if authentication is disabled for local development
    if current_app.config.get('DISABLE_AUTH', False):
        return redirect(url_for('main.index'))
    
    # Get the redirect URI
    if current_app.config.get('CLOUDFRONT_DOMAIN'):
        # Use CloudFront domain for production
        redirect_uri = f"https://{current_app.config['CLOUDFRONT_DOMAIN']}"
    else:
        # Use local domain for development
        redirect_uri = url_for('main.index', _external=True)
    
    # Get the Cognito logout URL
    logout_url = get_cognito_logout_url(redirect_uri)
    
    return redirect(logout_url)
