"""Security regression tests for the Flask UI.

Run from hotel_revenue_optimization_ui/, with no network and no AWS account:

    pip install -r requirements-dev.txt
    PYTHONPATH=. python -m pytest tests

ID tokens are signed with RSA keys generated here and checked against an in-memory JSON Web Key Set
through the real PyJWKClient key lookup. AWS calls are stubbed.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import runpy
import secrets
import time
from html import unescape
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlsplit

# The app reads its configuration from the environment when it is imported, so set a known environment
# first: no developer .env file, none of the app settings, and fake AWS credentials with no shared
# configuration, so that nothing here can reach a real AWS account.
os.environ['PYTHON_DOTENV_DISABLED'] = '1'
for _name in ('SECRET_KEY', 'FLASK_ENV', 'DISABLE_AUTH', 'AGENTCORE_RUNTIME_ARN', 'COGNITO_USER_POOL_ID',
              'COGNITO_APP_CLIENT_ID', 'COGNITO_CLIENT_ID', 'COGNITO_CLIENT_SECRET', 'COGNITO_DOMAIN',
              'AUTH_REDIRECT_URI', 'CLOUDFRONT_DOMAIN', 'SESSION_COOKIE_DOMAIN', 'SENDER_EMAIL',
              'HISTORY_TABLE_NAME', 'FLASK_RUN_HOST', 'AWS_PROFILE', 'AWS_DEFAULT_PROFILE', 'AWS_SESSION_TOKEN'):
    os.environ.pop(_name, None)
os.environ.update(AWS_ACCESS_KEY_ID='testing', AWS_SECRET_ACCESS_KEY='testing', AWS_DEFAULT_REGION='us-east-1',
                  AWS_CONFIG_FILE=os.devnull, AWS_SHARED_CREDENTIALS_FILE=os.devnull)

import jwt  # noqa: E402
import pytest  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402

from app import create_app  # noqa: E402
from app.api.agentcore import invoke_agentcore  # noqa: E402
from app.auth import tokens  # noqa: E402
from app.config import Config  # noqa: E402
from app.main import routes as main_routes  # noqa: E402
from app.services.email_report import EmailReportService  # noqa: E402

UI_DIR = Path(__file__).resolve().parents[1]

POOL_ID = 'us-east-1_TestPool1'
CLIENT_ID = 'test-app-client-id'
CLIENT_SECRET = 'test-app-client-secret-value'
ISSUER = f'https://cognito-idp.us-east-1.amazonaws.com/{POOL_ID}'
JWKS_URL = f'{ISSUER}/.well-known/jwks.json'
KID = 'pool-signing-key'
COGNITO_DOMAIN = 'test-domain.auth.us-east-1.amazoncognito.com'
REDIRECT_URI = 'https://app.example.com/auth/callback'

POOL_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ATTACKER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)

PRODUCTION_SETTINGS = {
    'SECRET_KEY': secrets.token_urlsafe(48),
    'COGNITO_USER_POOL_ID': POOL_ID,
    'COGNITO_APP_CLIENT_ID': CLIENT_ID,
    'COGNITO_CLIENT_SECRET': CLIENT_SECRET,
    'COGNITO_DOMAIN': COGNITO_DOMAIN,
    'AUTH_REDIRECT_URI': REDIRECT_URI,
    'AGENTCORE_RUNTIME_ARN': 'arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/test_agent-abcdefghij',
    'DISABLE_AUTH': False,
    # The test client talks plain HTTP to localhost
    'SESSION_COOKIE_SECURE': False,
}


# Tokens

def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def id_token_claims(**changes):
    now = int(time.time())
    claims = {
        'sub': 'verified-user-sub',
        'email': 'verified.user@example.com',
        'email_verified': True,
        'name': 'Verified User',
        'aud': CLIENT_ID,
        'iss': ISSUER,
        'token_use': 'id',
        'auth_time': now,
        'iat': now,
        'exp': now + 3600,
    }
    claims.update(changes)
    return claims


def sign(claims, key=POOL_KEY, kid=KID):
    return jwt.encode(claims, key, algorithm='RS256', headers={'kid': kid})


def unsigned_token(claims):
    header = b64url(json.dumps({'alg': 'none', 'typ': 'JWT', 'kid': KID}).encode())
    return f"{header}.{b64url(json.dumps(claims).encode())}."


def hs256_keyed_with_public_key(claims):
    """Algorithm confusion: an HMAC token whose secret is the pool's public key."""
    public_pem = POOL_KEY.public_key().public_bytes(serialization.Encoding.PEM,
                                                     serialization.PublicFormat.SubjectPublicKeyInfo)
    header = b64url(json.dumps({'alg': 'HS256', 'typ': 'JWT', 'kid': KID}).encode())
    signing_input = f"{header}.{b64url(json.dumps(claims).encode())}"
    signature = hmac.new(public_pem, signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{b64url(signature)}"


def claims_without(name):
    return {key: value for key, value in id_token_claims().items() if key != name}


UNTRUSTED_TOKENS = {
    'forged signature': lambda: sign(id_token_claims(), key=ATTACKER_KEY),
    'unsigned (alg none)': lambda: unsigned_token(id_token_claims()),
    'HS256 keyed with the public key': lambda: hs256_keyed_with_public_key(id_token_claims()),
    'unknown signing key': lambda: sign(id_token_claims(), key=ATTACKER_KEY, kid='attacker-key'),
    'wrong issuer': lambda: sign(id_token_claims(iss='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Other')),
    'wrong audience': lambda: sign(id_token_claims(aud='another-app-client')),
    'expired': lambda: sign(id_token_claims(iat=int(time.time()) - 7200, exp=int(time.time()) - 3600)),
    'access token': lambda: sign(id_token_claims(token_use='access')),
    'no expiry': lambda: sign(claims_without('exp')),
    'not a JWT': lambda: 'not-a-jwt',
}
untrusted_tokens = pytest.mark.parametrize('make_token', list(UNTRUSTED_TOKENS.values()), ids=list(UNTRUSTED_TOKENS))


class InMemoryJWKSClient(jwt.PyJWKClient):
    """PyJWKClient with its real key lookup, reading the user pool key set from memory, not the network."""

    def fetch_data(self):
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(POOL_KEY.public_key()))
        jwk.update(kid=KID, alg='RS256', use='sig')
        return {'keys': [jwk]}


@pytest.fixture(autouse=True)
def pool_jwks(monkeypatch):
    """Serve the user pool JWKS from memory; return the JWKS URLs the app asked for."""
    requested = []

    def get_jwks_client(url):
        requested.append(url)
        return InMemoryJWKSClient(url)

    monkeypatch.setattr(tokens, 'get_jwks_client', get_jwks_client)
    return requested


# Apps and clients

def production_app(**changes):
    settings = dict(PRODUCTION_SETTINGS)
    settings.update(changes)
    return create_app('production', settings)


@pytest.fixture
def client():
    """Production configuration, with CSRF checks off so that JSON posts need no token."""
    return production_app(WTF_CSRF_ENABLED=False).test_client()


def sign_in(client, **user):
    with client.session_transaction() as sess:
        sess['user'] = {'sub': 'verified-user-sub', 'email': 'verified.user@example.com', 'email_verified': True,
                        **user}
        sess['token_expiration'] = int(time.time()) + 600


def session_user(client):
    with client.session_transaction() as sess:
        return sess.get('user')


# 1. token verification

def test_valid_id_token_is_accepted(pool_jwks):
    app = production_app()
    with app.app_context():
        claims = tokens.verify_id_token(sign(id_token_claims()))
    assert claims['sub'] == 'verified-user-sub'
    assert pool_jwks == [JWKS_URL]


@untrusted_tokens
def test_untrusted_tokens_are_rejected(make_token):
    app = production_app()
    with app.app_context():
        with pytest.raises(tokens.TokenVerificationError):
            tokens.verify_id_token(make_token())


# 2. token_required

def test_protected_page_accepts_a_verified_bearer_token(client):
    response = client.get('/dashboard', headers={'Authorization': f'Bearer {sign(id_token_claims())}'})
    assert response.status_code == 200
    assert session_user(client)['sub'] == 'verified-user-sub'


@untrusted_tokens
def test_protected_page_rejects_untrusted_bearer_tokens(client, make_token):
    response = client.get('/dashboard', headers={'Authorization': f'Bearer {make_token()}'})
    assert response.status_code == 401
    assert session_user(client) is None


def test_id_token_cookie_is_not_accepted(client):
    client.set_cookie('id_token', sign(id_token_claims()))
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert urlsplit(response.headers['Location']).path == '/auth/login'


@pytest.mark.parametrize('expiration', [None, -60], ids=['no expiry in session', 'expired session'])
def test_session_identity_needs_an_unexpired_sign_in(client, expiration):
    with client.session_transaction() as sess:
        sess['user'] = {'sub': 'someone', 'email': 'someone@example.com'}
        if expiration is not None:
            sess['token_expiration'] = int(time.time()) + expiration
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert session_user(client) is None


def test_anonymous_user_is_sent_to_login_with_a_relative_next(client):
    response = client.get('/history?page=2')
    assert response.status_code == 302
    location = urlsplit(response.headers['Location'])
    assert location.path == '/auth/login'
    assert parse_qs(location.query)['next'] == ['/history?page=2']


# 3. No sign-in from tokens in the URL (implicit flow removed)

def test_callback_without_a_code_signs_nobody_in(client):
    # A link such as /auth/callback#id_token=<someone's valid token> reaches the server as a callback without
    # a code; it must not render a page that signs the visitor in with that token
    response = client.get('/auth/callback')
    assert response.status_code == 400
    assert 'process-token' not in response.get_data(as_text=True)
    assert session_user(client) is None


def test_callback_with_a_token_in_the_query_signs_nobody_in(client):
    response = client.get('/auth/callback', query_string={'id_token': sign(id_token_claims())})
    assert response.status_code == 400
    assert session_user(client) is None


def test_process_token_endpoint_is_gone(client):
    response = client.post('/auth/process-token', json={'id_token': sign(id_token_claims())})
    assert response.status_code in (404, 405)
    assert session_user(client) is None


# 4. OAuth state and PKCE

def authorize_url(login_page):
    match = re.search(r'href="([^"]*/oauth2/authorize\?[^"]*)"', login_page.get_data(as_text=True))
    assert match, 'the login page has no Cognito authorize link'
    return urlsplit(unescape(match.group(1)))


def test_login_starts_the_code_flow_with_state_and_pkce(client):
    response = client.get('/auth/login')
    assert response.status_code == 200
    url = authorize_url(response)
    params = {key: values[0] for key, values in parse_qs(url.query).items()}
    with client.session_transaction() as sess:
        state, verifier = sess['oauth_state'], sess['pkce_verifier']
    assert (url.scheme, url.netloc, url.path) == ('https', COGNITO_DOMAIN, '/oauth2/authorize')
    assert params['response_type'] == 'code'
    assert params['client_id'] == CLIENT_ID
    assert params['redirect_uri'] == REDIRECT_URI
    assert params['state'] == state and len(state) >= 32
    assert params['code_challenge_method'] == 'S256'
    assert params['code_challenge'] == b64url(hashlib.sha256(verifier.encode()).digest())
    assert 43 <= len(verifier) <= 128


@pytest.mark.parametrize('state', ['attacker-state', ''], ids=['wrong state', 'empty state'])
def test_callback_rejects_a_code_with_the_wrong_state(client, state):
    client.get('/auth/login')
    with mock.patch('app.auth.routes.requests.post') as token_endpoint:
        response = client.get('/auth/callback', query_string={'code': 'attacker-code', 'state': state})
    assert response.status_code == 400
    token_endpoint.assert_not_called()
    assert session_user(client) is None


def test_callback_rejects_a_code_when_this_browser_started_no_sign_in(client):
    with mock.patch('app.auth.routes.requests.post') as token_endpoint:
        response = client.get('/auth/callback', query_string={'code': 'attacker-code', 'state': 'attacker-state'})
    assert response.status_code == 400
    token_endpoint.assert_not_called()
    assert session_user(client) is None


def token_endpoint_response(id_token):
    response = mock.Mock(status_code=200)
    response.json.return_value = {'id_token': id_token, 'access_token': 'opaque-access', 'token_type': 'Bearer'}
    return response


def test_callback_redeems_the_code_with_pkce_and_signs_in_from_the_verified_id_token(client, caplog):
    client.get('/auth/login', query_string={'next': '/history'})
    with client.session_transaction() as sess:
        state, verifier = sess['oauth_state'], sess['pkce_verifier']
    with caplog.at_level(logging.INFO):
        with mock.patch('app.auth.routes.requests.post',
                        return_value=token_endpoint_response(sign(id_token_claims()))) as token_endpoint:
            response = client.get('/auth/callback', query_string={'code': 'the-authorization-code', 'state': state})

    assert response.status_code == 302
    assert response.headers['Location'] == '/history'
    args, kwargs = token_endpoint.call_args
    assert args[0] == f'https://{COGNITO_DOMAIN}/oauth2/token'
    assert kwargs['data'] == {'grant_type': 'authorization_code', 'code': 'the-authorization-code',
                              'redirect_uri': REDIRECT_URI, 'code_verifier': verifier}
    assert kwargs['auth'] == (CLIENT_ID, CLIENT_SECRET)
    assert kwargs['timeout']
    with client.session_transaction() as sess:
        assert sess['user']['sub'] == 'verified-user-sub'
        assert 'oauth_state' not in sess and 'pkce_verifier' not in sess

    # 5. Nothing secret is logged: not the client secret, its Basic header, the code, the state or the verifier
    basic_header = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()
    for secret_value in (CLIENT_SECRET, CLIENT_SECRET[:10], basic_header, 'the-authorization-code', state, verifier):
        assert secret_value not in caplog.text


def test_callback_rejects_an_id_token_that_fails_verification(client):
    client.get('/auth/login')
    with client.session_transaction() as sess:
        state = sess['oauth_state']
    forged = sign(id_token_claims(sub='attacker-chosen-sub'), key=ATTACKER_KEY)
    with mock.patch('app.auth.routes.requests.post', return_value=token_endpoint_response(forged)):
        response = client.get('/auth/callback', query_string={'code': 'the-authorization-code', 'state': state})
    assert response.status_code == 401
    assert session_user(client) is None


# 6. open redirect through next

@pytest.mark.parametrize('target, expected', [
    ('/history', '/history'),
    ('/natural_language?query=pricing', '/natural_language?query=pricing'),
    ('https://evil.example/login', '/'),
    ('//evil.example', '/'),
    ('/\\evil.example', '/'),
    ('\\\\evil.example', '/'),
    ('/\t/evil.example', '/'),
    ('javascript:alert(1)', '/'),
    ('evil.example', '/'),
])
def test_login_next_redirects_only_to_paths_on_this_site(target, expected):
    # With DISABLE_AUTH (local development) /auth/login signs in at once and redirects to next
    response = create_app('testing').test_client().get('/auth/login', query_string={'next': target})
    assert response.status_code == 302
    assert response.headers['Location'] == expected


def test_signed_in_user_is_not_redirected_to_another_site(client):
    sign_in(client)
    response = client.get('/auth/login', query_string={'next': '//evil.example'})
    assert response.status_code == 302
    assert response.headers['Location'] == '/'


# 7. markdown from the agent or the user

XSS_REPORT = '\n\n'.join([
    '# Revenue plan',
    '| Room | Rate |\n|---|--:|\n| Suite | 450 |',
    '<script>alert("xss-script")</script>',
    '<img src="https://evil.example/pixel.png" onerror="alert(\'xss-img\')">',
    '<p onclick="alert(\'xss-click\')">Click</p>',
    '[Book now](javascript:alert(1))',
    '<svg onload="alert(\'xss-svg\')"></svg>',
    '<iframe src="https://evil.example/frame"></iframe>',
])


def test_markdown_is_sanitized_before_it_is_marked_safe():
    html = main_routes.render_markdown(XSS_REPORT)
    lowered = html.lower()
    for needle in ('<script', 'onerror', 'onclick', 'onload', 'javascript:', '<img', '<svg', '<iframe',
                   'xss-', 'evil.example'):
        assert needle not in lowered
    # Ordinary report markdown still renders
    assert '<h1>Revenue plan</h1>' in html
    assert '<table>' in html and '<td align="right">450</td>' in html


def test_history_page_does_not_render_markup_from_the_stored_report(monkeypatch):
    stored = {'user_id': 'local-development-user', 'timestamp': '2026-11-24T10:00:00',
              'query_summary': 'Optimize revenue', 'result_status': 'success',
              'result_data': {'status': 'success', 'markdown_content': XSS_REPORT}}
    monkeypatch.setattr(main_routes.history_service, 'get_query_result', lambda user_id, timestamp: stored)
    response = create_app('testing').test_client().get('/history/2026-11-24T10:00:00')
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert '<h1>Revenue plan</h1>' in page
    for marker in ('xss-script', 'xss-img', 'xss-click', 'xss-svg', 'javascript:alert', 'evil.example'):
        assert marker not in page


# 8. email reports

def test_email_html_escapes_the_query_and_the_report():
    html = EmailReportService()._format_html_content({'report': '<script>alert("report")</script>'},
                                                     '<img src=x onerror=alert("query")>')
    assert '<script' not in html and '<img' not in html
    assert '&lt;img src=x onerror=alert(&quot;query&quot;)&gt;' in html
    assert '&lt;script&gt;' in html


@pytest.fixture
def sent_emails(monkeypatch):
    """Stub SES and the history table; return the SendEmail requests."""
    sent = []
    stored = {'user_id': 'verified-user-sub', 'timestamp': '2026-11-24T10:00:00',
              'query_summary': '<b onmouseover="alert(1)">Plan</b>',
              'result_data': {'status': 'success', 'markdown_content': '<script>alert(2)</script>'}}
    monkeypatch.setattr(main_routes.email_service, 'sender_email', 'reports@example.com')
    monkeypatch.setattr(main_routes.email_service.ses, 'send_email',
                        lambda **request: sent.append(request) or {'MessageId': 'test-message'})
    monkeypatch.setattr(main_routes.history_service, 'get_query_result',
                        lambda user_id, timestamp: stored if user_id == 'verified-user-sub' else None)
    return sent


def test_email_report_goes_only_to_the_signed_in_users_verified_address(client, sent_emails):
    sign_in(client)
    response = client.post('/send-email-report',
                           json={'timestamp': '2026-11-24T10:00:00', 'email': 'someone.else@example.net'})
    assert response.status_code == 200
    assert len(sent_emails) == 1
    assert sent_emails[0]['Source'] == 'reports@example.com'
    assert sent_emails[0]['Destination'] == {'ToAddresses': ['verified.user@example.com']}
    html_body = sent_emails[0]['Message']['Body']['Html']['Data']
    assert '<b onmouseover' not in html_body and '<script' not in html_body
    assert '&lt;b onmouseover=' in html_body


def test_email_report_needs_a_verified_address(client, sent_emails):
    sign_in(client, email='unverified@example.com', email_verified=False)
    response = client.post('/send-email-report', json={'timestamp': '2026-11-24T10:00:00'})
    assert response.status_code == 403
    assert sent_emails == []


def test_email_report_is_off_without_a_sender_address(client, sent_emails, monkeypatch):
    monkeypatch.setattr(main_routes.email_service, 'sender_email', '')
    sign_in(client)
    response = client.post('/send-email-report', json={'timestamp': '2026-11-24T10:00:00'})
    assert response.status_code == 503
    assert sent_emails == []


# 9. production configuration

def test_production_refuses_to_start_when_secret_key_is_not_set():
    settings = {key: value for key, value in PRODUCTION_SETTINGS.items() if key != 'SECRET_KEY'}
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app('production', settings)


@pytest.mark.parametrize('secret_key', [
    None,
    '',
    'dev-key-please-change-in-production',
    'your-secret-key-here',
    'hotel-revenue-optimization-prod-production-key-2025',
    'short-random-Xy9',
], ids=['none', 'empty', 'development default', '.env.example placeholder', 'old template-derived key', 'too short'])
def test_production_refuses_a_weak_secret_key(secret_key):
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        production_app(SECRET_KEY=secret_key)


def test_production_starts_with_a_strong_secret_key():
    app = production_app()
    assert app.config['SECRET_KEY'] == PRODUCTION_SETTINGS['SECRET_KEY']


def test_agentcore_runtime_arn_has_no_default_and_is_required_in_production():
    assert Config.AGENTCORE_RUNTIME_ARN == ''
    with pytest.raises(RuntimeError, match='AGENTCORE_RUNTIME_ARN'):
        production_app(AGENTCORE_RUNTIME_ARN='')


def test_missing_agentcore_runtime_arn_gives_a_clear_error():
    app = create_app('testing')
    with app.app_context():
        with pytest.raises(RuntimeError, match='AGENTCORE_RUNTIME_ARN is not set'):
            invoke_agentcore({'query_type': 'natural_language', 'query': 'hello'})


# 10. local development server

@pytest.mark.parametrize('host, expected_host, expected_debug', [
    (None, '127.0.0.1', True),
    ('0.0.0.0', '0.0.0.0', False),
], ids=['default host', 'all interfaces'])
def test_local_server_listens_on_loopback_and_never_exposes_the_debugger(monkeypatch, host, expected_host,
                                                                         expected_debug):
    if host:
        monkeypatch.setenv('FLASK_RUN_HOST', host)
    with mock.patch('flask.Flask.run') as run:
        runpy.run_path(str(UI_DIR / 'app.py'), run_name='__main__')
    assert run.call_args.kwargs['host'] == expected_host
    assert run.call_args.kwargs['debug'] is expected_debug


# 11. container image and ECS template

def test_dockerfile_uses_a_public_base_image_and_a_non_root_user():
    dockerfile = (UI_DIR / 'Dockerfile').read_text()
    assert dockerfile.splitlines()[0] == 'FROM public.ecr.aws/docker/library/python:3.12-slim'
    users = re.findall(r'^USER\s+(\S+)', dockerfile, re.MULTILINE)
    assert users and users[-1] not in ('root', '0')
    assert 'AGENTCORE_RUNTIME_ARN=' not in dockerfile


def test_ecs_template_injects_secrets_and_grants_no_managed_bedrock_policy():
    template = (UI_DIR / 'infrastructure' / 'cloudformation' / 'ecs.yaml').read_text()
    assert 'AmazonBedrockFullAccess' not in template
    assert 'production-key-2025' not in template
    assert 'resolve:secretsmanager:CognitoClientSecret' not in template
    environment, secrets_section = template.split('          Secrets:\n', 1)
    secrets_section = secrets_section.split('          LogConfiguration:', 1)[0]
    assert '- Name: SECRET_KEY' in secrets_section and '- Name: COGNITO_CLIENT_SECRET' in secrets_section
    assert '- Name: SECRET_KEY' not in environment and '- Name: COGNITO_CLIENT_SECRET' not in environment


# Page smoke test

@pytest.mark.parametrize('path', ['/health', '/', '/dashboard', '/help', '/natural_language', '/structured_form',
                                  '/history'])
def test_pages_render_in_local_development_mode(path):
    response = create_app('testing').test_client().get(path)
    assert response.status_code == 200


def test_signed_in_pages_render_in_production(client):
    sign_in(client)
    for path in ('/dashboard', '/natural_language', '/structured_form', '/history', '/help'):
        assert client.get(path).status_code == 200


def test_form_post_without_csrf_token_is_rejected_in_production():
    client = production_app().test_client()
    sign_in(client)
    response = client.post('/natural_language', data={'query': 'Optimize pricing'})
    assert response.status_code == 400
