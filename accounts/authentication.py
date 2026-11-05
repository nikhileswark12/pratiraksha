from django.core.cache import cache
from dj_rest_auth.jwt_auth import JWTCookieAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class RevocationCheckMixin:
    def get_user(self, validated_token):
        token_jti = validated_token.get("jti")
        if not token_jti or not cache.get(f"jti_{token_jti}"):
            raise AuthenticationFailed("Token has been revoked or expired.")
        user = super().get_user(validated_token)
        if not user.is_active:
            raise AuthenticationFailed("User account is inactive.")
        return user


class RevocableJWTAuthentication(RevocationCheckMixin, JWTAuthentication):
    pass


class RevocableJWTCookieAuthentication(RevocationCheckMixin, JWTCookieAuthentication):
    pass
