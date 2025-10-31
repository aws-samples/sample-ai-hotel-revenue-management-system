from flask import render_template, redirect, url_for, request, session, current_app, jsonify
from app.auth import bp
from app.auth.cognito import get_cognito_login_url, get_cognito_logout_url
import logging
import time

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

@bp.route('/login')
def login():
    """Login page"""
    # Check if authentication is disabled for local development
    if current_app.config.get('DISABLE_AUTH', False):
        logger.info("Authentication is disabled for local development")
        # Add a mock user to the session for development
        session['user'] = {
            'sub': 'local-development-user',
            'email': 'dev@example.com',
            'name': 'Local Developer'
        }
        next_url = request.args.get('next', url_for('main.index'))
        return redirect(next_url)
    
    # Check if user is already logged in
    if 'user' in session:
        next_url = request.args.get('next', url_for('main.index'))
        return redirect(next_url)
    
    # Get the redirect URI
    if current_app.config.get('AUTH_REDIRECT_URI'):
        # Use the configured redirect URI
        redirect_uri = current_app.config.get('AUTH_REDIRECT_URI')
        logger.info(f"Using configured redirect URI: {redirect_uri}")
    elif current_app.config.get('CLOUDFRONT_DOMAIN'):
        # Use CloudFront domain for production
        redirect_uri = f"https://{current_app.config['CLOUDFRONT_DOMAIN']}/auth/callback"
        logger.info(f"Using CloudFront redirect URI: {redirect_uri}")
    else:
        # Use local domain for development
        redirect_uri = url_for('auth.callback', _external=True)
        logger.info(f"Using local redirect URI: {redirect_uri}")
    
    # Get the Cognito login URL
    login_url = get_cognito_login_url(redirect_uri)
    
    return render_template('auth/login.html', login_url=login_url)

@bp.route('/callback')
def callback():
    """Callback endpoint for Cognito authentication"""
    # Check if this is a code flow callback
    code = request.args.get('code')
    if code:
        logger.info("Received authorization code from Cognito")
        # Log all request parameters for debugging
        logger.info(f"Request args: {request.args}")
        
        try:
            # Exchange the code for tokens
            token_endpoint = f"https://{current_app.config['COGNITO_DOMAIN']}/oauth2/token"
            client_id = current_app.config.get('COGNITO_CLIENT_ID') or current_app.config.get('COGNITO_APP_CLIENT_ID')
            client_secret = current_app.config.get('COGNITO_CLIENT_SECRET', '5lvq8u7vsulcnp6l5pfquitf3ta9gkc74ghu9414972cgjnijq3')
            
            if current_app.config.get('AUTH_REDIRECT_URI'):
                redirect_uri = current_app.config.get('AUTH_REDIRECT_URI')
            elif current_app.config.get('CLOUDFRONT_DOMAIN'):
                redirect_uri = f"https://{current_app.config['CLOUDFRONT_DOMAIN']}/auth/callback"
            else:
                redirect_uri = url_for('auth.callback', _external=True)
            
            logger.info(f"Token endpoint: {token_endpoint}")
            logger.info(f"Client ID: {client_id}")
            logger.info(f"Redirect URI: {redirect_uri}")
            
            import requests
            import base64
            
            # Create the Authorization header with Basic auth using client_id and client_secret
            auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('utf-8')
            
            # Debug logging
            logger.info(f"Client Secret (first 10 chars): {client_secret[:10]}...")
            logger.info(f"Auth header: Basic {auth_header}")
            
            token_response = requests.post(
                token_endpoint,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Basic {auth_header}'
                }
            )
            
            if token_response.status_code == 200:
                tokens = token_response.json()
                id_token = tokens.get('id_token')
                access_token = tokens.get('access_token')
                
                # Get user info from the ID token
                import jwt
                import base64
                import json
                
                # Parse the ID token payload
                id_token_parts = id_token.split('.')
                if len(id_token_parts) >= 2:
                    # Fix padding for base64 decoding
                    payload = id_token_parts[1]
                    payload += '=' * (4 - len(payload) % 4) if len(payload) % 4 != 0 else ''
                    
                    try:
                        decoded_payload = base64.b64decode(payload)
                        user_info = json.loads(decoded_payload)
                        
                        # Log user info for debugging (excluding sensitive data)
                        logger.info(f"User info from token: email={user_info.get('email')}, name={user_info.get('name')}, given_name={user_info.get('given_name')}, family_name={user_info.get('family_name')}")
                        
                        # Store user info in session
                        session.permanent = True
                        session['user'] = {
                            'sub': user_info.get('sub', 'unknown'),
                            'email': user_info.get('email', 'unknown@example.com'),
                            'name': user_info.get('name', user_info.get('email', 'User')),
                            'given_name': user_info.get('given_name', ''),
                            'family_name': user_info.get('family_name', '')
                        }
                        
                        # Store tokens in session
                        session['id_token'] = id_token
                        session['access_token'] = access_token
                        
                        # Set token expiration (1 hour from now or use exp from token)
                        if 'exp' in user_info:
                            session['token_expiration'] = user_info['exp']
                        else:
                            session['token_expiration'] = int(time.time()) + (24 * 60 * 60)
                        
                        logger.info(f"User added to session: {session['user'].get('email')}")
                        logger.info(f"Token expiration: {session.get('token_expiration')}")
                        
                    except Exception as e:
                        logger.error(f"Error decoding ID token: {e}")
                        # Return error instead of using hardcoded values
                        return render_template('auth/error.html', 
                                              error="Authentication Error", 
                                              error_description="Failed to decode user information from token. Please try again or contact support.")
                else:
                    logger.error("Invalid ID token format")
                    # Return error instead of using hardcoded values
                    return render_template('auth/error.html', 
                                          error="Authentication Error", 
                                          error_description="Invalid token format received. Please try again or contact support.")
            else:
                logger.error(f"Error exchanging code for tokens: {token_response.status_code} {token_response.text}")
                # Return error instead of using hardcoded values
                return render_template('auth/error.html', 
                                      error="Authentication Error", 
                                      error_description=f"Failed to authenticate with Cognito. Error: {token_response.text}")
                
        except Exception as e:
            logger.error(f"Error in token exchange: {e}")
            # Return error instead of using hardcoded values
            return render_template('auth/error.html', 
                                  error="Authentication Error", 
                                  error_description="An unexpected error occurred during authentication. Please try again or contact support.")
        
        # Set a session cookie that will work with CloudFront
        response = redirect(url_for('main.index'))
        return response
    
    # If there's an error parameter, log it
    error = request.args.get('error')
    if error:
        logger.error(f"Error in Cognito callback: {error}")
        logger.error(f"Error description: {request.args.get('error_description')}")
        return render_template('auth/error.html', error=error, error_description=request.args.get('error_description'))
    
    # This endpoint is used for the implicit grant flow
    # The tokens are returned in the URL fragment, which is processed by JavaScript
    return render_template('auth/callback.html', next_url=url_for('main.index'))

@bp.route('/process-token', methods=['POST'])
def process_token():
    """Process the token received from Cognito"""
    data = request.get_json()
    
    if not data or 'id_token' not in data:
        return jsonify({'error': 'Invalid request'}), 400
    
    # Make the session permanent
    session.permanent = True
    
    # Store the tokens in the session
    session['id_token'] = data['id_token']
    session['access_token'] = data.get('access_token')
    
    # Set token expiration (24 hours from now if not provided)
    if data.get('expires_at'):
        session['token_expiration'] = data.get('expires_at')
    else:
        session['token_expiration'] = int(time.time()) + (24 * 60 * 60)
    
    # Store user info in session
    session['user'] = {
        'sub': data.get('sub'),
        'email': data.get('email'),
        'name': data.get('name', data.get('email', 'User'))
    }
    
    logger.info(f"Token processed and user added to session: {session.get('user', {}).get('email')}")
    logger.info(f"Session expiration: {session.get('token_expiration')}")
    
    return jsonify({'success': True, 'redirect': url_for('main.index')})

@bp.route('/logout')
def logout():
    """Logout endpoint"""
    # Clear the session
    session.pop('user', None)
    session.pop('id_token', None)
    session.pop('access_token', None)
    session.pop('token_expiration', None)
    
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
