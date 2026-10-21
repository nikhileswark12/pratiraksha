from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_string):
    try:
        access_token = AccessToken(token_string)
        user_id = access_token['id']
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    """
    Authenticate WebSockets with a JWT supplied as a WebSocket subprotocol,
    avoiding credentials in URL query strings, browser history, and access logs.
    The client offers ["pratiraksha", "<access-token>"].
    """
    async def __call__(self, scope, receive, send):
        offered_protocols = scope.get("subprotocols", [])
        token = next(
            (protocol for protocol in offered_protocols if protocol != "pratiraksha"),
            None,
        )
        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()
        return await super().__call__(scope, receive, send)
