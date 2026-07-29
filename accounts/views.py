from datetime import timedelta
import uuid
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import authenticate
from rest_framework import status, views, generics, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken

from .models import User
from .serializers import RegisterSerializer, UserSerializer

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
            return Response(tokens, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

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
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # We must validate the jti of the incoming refresh token against Redis
            refresh_token = request.data.get('refresh')
            try:
                token = RefreshToken(refresh_token)
                jti = token.get('jti')
                if not jti or not cache.get(f"jti_{jti}"):
                    raise InvalidToken("Token has been revoked or expired.")
                
                # We should issue a new JTI for the newly created tokens (which SimpleJWT handles automatically for rotation, but we have ROTATE_REFRESH_TOKENS=False).
                # Actually, simplejwt refresh view just issues a new access token if ROTATE=False.
                # Let's customize it to include our custom claims in the new access token.
                # SimpleJWT copies claims from the refresh token to the new access token if configured.
                # It's cleaner to decode the new token, add claims and encode, or rely on SimpleJWT's TokenUser.
                pass
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        return response

class MeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
