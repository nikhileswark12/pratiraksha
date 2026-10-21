from datetime import timedelta
import uuid
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import authenticate
from rest_framework import status, views, generics, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

from .models import User
from .serializers import RegisterSerializer, UserSerializer
from pratiraksha.utils import log_compliance_event

def get_tokens_for_user(user, remember_me=False):
    refresh = RefreshToken.for_user(user)
    
    # Custom payload
    refresh['role'] = user.role
    refresh['name'] = user.name
    
    # Generate a unique jti
    jti = str(uuid.uuid4())
    refresh['jti'] = jti
    refresh.access_token['jti'] = jti
    refresh.access_token['role'] = user.role
    refresh.access_token['name'] = user.name

    if remember_me:
        refresh.set_exp(lifetime=timedelta(days=30))
    else:
        refresh.set_exp(lifetime=timedelta(days=7))

    # Store jti in Redis (valid for the token's lifetime)
    exp = refresh['exp'] - timezone.now().timestamp()
    if exp > 0:
        cache.set(f"jti_{jti}", "valid", timeout=int(exp))

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            
            log_compliance_event(
                actor=str(user.id),
                action="role_assigned_at_registration",
                resource_type="auth",
                extra_data={"role": user.role, "hospital_id": str(user.hospital_id) if user.hospital_id else None}
            )
            
            return Response(tokens, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        remember_me = request.data.get('remember_me', False)

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check user exists for lockout logic
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        # Lockout check
        if user_obj.account_locked_until and user_obj.account_locked_until > timezone.now():
            return Response({"error": "Account is temporarily locked due to multiple failed login attempts."}, status=status.HTTP_403_FORBIDDEN)

        user = authenticate(request, email=email, password=password)

        if user:
            # Check role (admin not allowed via this endpoint)
            if user.role not in ['operator', 'hospital_manager']:
                return Response({"error": "Unauthorized role for this endpoint."}, status=status.HTTP_403_FORBIDDEN)

            # Reset failed attempts
            user.failed_login_attempts = 0
            user.account_locked_until = None
            user.last_login = timezone.now()
            user.save(update_fields=['failed_login_attempts', 'account_locked_until', 'last_login'])

            tokens = get_tokens_for_user(user, remember_me)
            
            from pratiraksha.utils import log_activity
            log_activity(
                actor=str(user.id),
                action="login",
                resource_type="user",
                resource_id=str(user.id)
            )
            
            return Response(tokens, status=status.HTTP_200_OK)
        else:
            # Increment failed attempts
            user_obj.failed_login_attempts += 1
            if user_obj.failed_login_attempts >= 5:
                user_obj.account_locked_until = timezone.now() + timedelta(minutes=15)
            user_obj.save(update_fields=['failed_login_attempts', 'account_locked_until'])
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        try:
            if not refresh_token:
                raise InvalidToken("Refresh token is required.")
            incoming = RefreshToken(refresh_token)
            incoming_jti = incoming.get('jti')
            if not incoming_jti or not cache.get(f"jti_{incoming_jti}"):
                raise InvalidToken("Token has been revoked or expired.")
        except Exception:
            return Response({"error": "Invalid or revoked refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            try:
                if response.data.get('refresh'):
                    rotated = RefreshToken(response.data['refresh'])
                    rotated_jti = rotated.get('jti')
                    refresh_expires_in = int(rotated['exp'] - timezone.now().timestamp())
                    if rotated_jti and refresh_expires_in > 0:
                        cache.set(f"jti_{rotated_jti}", "valid", timeout=refresh_expires_in)
                        # Refresh tokens are single-use once rotation succeeds.
                        cache.delete(f"jti_{incoming_jti}")
                if response.data.get('access'):
                    access = AccessToken(response.data['access'])
                    access_jti = access.get('jti')
                    access_expires_in = int(access['exp'] - timezone.now().timestamp())
                    if access_jti and access_expires_in > 0:
                        cache.set(f"jti_{access_jti}", "valid", timeout=access_expires_in)
            except Exception:
                return Response({"error": "Failed to register rotated token identifiers."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return response

class MeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class CachedSocialLoginView(SocialLoginView):
    """Register SSO-issued token JTIs for refresh and WebSocket revocation checks."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK and isinstance(response.data, dict):
            try:
                for key, token_class in (("access", AccessToken), ("refresh", RefreshToken)):
                    token_string = response.data.get(key)
                    if not token_string:
                        continue
                    token = token_class(token_string)
                    ttl = int(token["exp"] - timezone.now().timestamp())
                    token_jti = token.get("jti")
                    if token_jti and ttl > 0:
                        cache.set(f"jti_{token_jti}", "valid", timeout=ttl)
            except Exception:
                return Response(
                    {"error": "Unable to initialize the session. Please retry."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        return response


class GoogleLogin(CachedSocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:3000/auth/google/callback'
    client_class = OAuth2Client

class GitHubLogin(CachedSocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = 'http://localhost:3000/auth/github/callback'
    client_class = OAuth2Client
