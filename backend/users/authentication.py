from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import Token


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
