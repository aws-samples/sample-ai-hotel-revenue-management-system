"""Verification of Amazon Cognito user pool ID tokens.

A token is trusted only when its RS256 signature verifies against a key from the user pool's JSON Web
Key Set (JWKS) and its issuer, audience (the app client ID), token use and expiry are the expected ones.
See https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
"""
import logging
from functools import lru_cache

import jwt
from flask import current_app

logger = logging.getLogger(__name__)

# Cognito signs user pool tokens with RS256. Listing it alone rejects "none", HS256 and other algorithms.
ALLOWED_ALGORITHMS = ['RS256']
# Tolerated clock difference, in seconds, when checking exp and iat
CLOCK_SKEW_SECONDS = 30
REQUIRED_CLAIMS = ['exp', 'iat', 'iss', 'aud', 'sub', 'token_use']


class TokenVerificationError(Exception):
    """The token is missing or malformed, is not signed by the user pool, or has the wrong claims."""


@lru_cache(maxsize=8)
def get_jwks_client(jwks_url):
    """Return the JWKS client for a user pool, created once and reused so the key set is cached."""
    return jwt.PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600, timeout=5)


def user_pool_issuer(app_config):
    """Return the issuer URL of the configured user pool, or None if no pool is configured."""
    pool_id = app_config.get('COGNITO_USER_POOL_ID')
    if not pool_id:
        return None
    # A user pool ID starts with its Region, for example us-east-1_AbCdEf123
    region = pool_id.split('_', 1)[0] if '_' in pool_id else app_config.get('COGNITO_REGION')
    return f'https://cognito-idp.{region}.amazonaws.com/{pool_id}'


def verify_id_token(token):
    """Verify a Cognito ID token for this app client and return its claims.

    Raises TokenVerificationError when the token must not be trusted.
    """
    app_config = current_app.config
    issuer = user_pool_issuer(app_config)
    client_id = app_config.get('COGNITO_CLIENT_ID') or app_config.get('COGNITO_APP_CLIENT_ID')
    if not issuer or not client_id:
        raise TokenVerificationError('the Cognito user pool or app client is not configured')
    if not token or not isinstance(token, str):
        raise TokenVerificationError('no token')

    try:
        signing_key = get_jwks_client(f'{issuer}/.well-known/jwks.json').get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=ALLOWED_ALGORITHMS,
            issuer=issuer,
            audience=client_id,
            leeway=CLOCK_SKEW_SECONDS,
            options={'require': REQUIRED_CLAIMS},
        )
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        # PyJWTError covers bad signatures, unknown keys, wrong issuer or audience, expiry and malformed
        # tokens. The exception class is enough to diagnose; the token itself is never logged.
        raise TokenVerificationError(exc.__class__.__name__) from exc

    if claims.get('token_use') != 'id':
        raise TokenVerificationError('not an ID token')
    return claims
