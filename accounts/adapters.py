from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework.exceptions import ValidationError
from .models import User
from pratiraksha.utils import log_compliance_event


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        # Validate before persisting anything. SSO self-registration follows the
        # same least-privilege policy as the public registration endpoint.
        role = request.data.get('role', 'operator')
        hospital_id = request.data.get('hospitalId')
        if role != 'operator':
            raise ValidationError({
                "role": "SSO self-registration is limited to operator accounts. "
                        "Hospital-manager accounts must be provisioned by an administrator."
            })
        if hospital_id is not None:
            raise ValidationError({
                "hospitalId": "Must be omitted for operator self-registration."
            })

        # Set required fields before the parent adapter saves the user.
        sociallogin.user.role = 'operator'
        sociallogin.user.hospital = None
        sociallogin.user.tenant = None
        user = super().save_user(request, sociallogin, form)

        log_compliance_event(
            actor=str(user.id),
            action="role_assigned_at_sso_registration",
            resource_type="auth",
            extra_data={"role": user.role, "hospital_id": None},
        )
        return user
