from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from rest_framework.exceptions import ValidationError
from hospitals.models import Hospital
from .models import User
from pratiraksha.utils import log_compliance_event

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        
        # When saving a new user via SSO, we must extract role and hospitalId from the request data
        data = request.data
        role = data.get('role')
        hospital_id = data.get('hospitalId')
        
        # Validate exactly like RegisterSerializer
        if role not in dict(User.ROLE_CHOICES).keys():
            raise ValidationError({"role": "Role must be 'operator' or 'hospital_manager'."})
            
        if role == 'hospital_manager':
            if not hospital_id:
                raise ValidationError({"hospitalId": "Required for hospital_manager role."})
            if not Hospital.objects.filter(id=hospital_id).exists():
                raise ValidationError({"hospitalId": "Invalid hospital ID."})
            user.hospital_id = hospital_id
        elif role == 'operator':
            if hospital_id is not None:
                raise ValidationError({"hospitalId": "Must be null for operator role."})
                
        user.role = role
        user.save()
        
        log_compliance_event(
            actor=str(user.id),
            action="role_assigned_at_sso_registration",
            resource_type="auth",
            extra_data={"role": user.role, "hospital_id": str(user.hospital_id) if user.hospital_id else None}
        )
        
        return user
