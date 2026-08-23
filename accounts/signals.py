import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, social_account_updated
from pratiraksha.utils import log_compliance_event

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_compliance_event(
        actor=str(user.id),
        action="login",
        resource_type="auth",
        extra_data={"method": "standard"}
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_compliance_event(
            actor=str(user.id),
            action="logout",
            resource_type="auth"
        )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    email = credentials.get('email', 'unknown')
    log_compliance_event(
        actor="system",
        action="login_failed",
        resource_type="auth",
        extra_data={"email": email}
    )

@receiver(social_account_added)
def log_social_account_added(sender, request, sociallogin, **kwargs):
    user = sociallogin.user
    log_compliance_event(
        actor=str(user.id),
        action="sso_account_linked",
        resource_type="auth",
        extra_data={"provider": sociallogin.account.provider}
    )

@receiver(social_account_updated)
def log_social_account_updated(sender, request, sociallogin, **kwargs):
    user = sociallogin.user
    log_compliance_event(
        actor=str(user.id),
        action="sso_account_updated",
        resource_type="auth",
        extra_data={"provider": sociallogin.account.provider}
    )
