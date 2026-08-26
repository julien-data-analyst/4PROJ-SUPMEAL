from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import Token


class BlacklistAwareJWTScheme(SimpleJWTScheme):
    """Tells drf-spectacular to document ``BlacklistAwareJWTAuthentication`` the same way
    it already documents plain ``JWTAuthentication`` (bearer JWT security scheme).

    drf-spectacular's built-in extension only matches the exact
    ``rest_framework_simplejwt.authentication.JWTAuthentication`` class, not subclasses -
    without this, every authenticated endpoint's schema would silently lose its "Authorize"
    padlock/security requirement now that this subclass is the project's default.
    """

    target_class = "users.authentication.BlacklistAwareJWTAuthentication"


class BlacklistAwareJWTAuthentication(JWTAuthentication):
    """JWTAuthentication that also rejects blacklisted access tokens.

    Simple JWT's blacklist app only consults ``BlacklistedToken`` when a
    ``RefreshToken`` is verified - access tokens are stateless and stay valid
    until they expire naturally. ``LogoutView`` blacklists the current access
    token's jti the same way it blacklists the refresh token's, so this
    override makes access-token validation consult that table too.
    """

    def get_validated_token(self, raw_token: bytes) -> Token:
        validated_token = super().get_validated_token(raw_token)
        if BlacklistedToken.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            token__jti=validated_token["jti"]
        ).exists():
            raise InvalidToken("Token is blacklisted.")
        return validated_token
