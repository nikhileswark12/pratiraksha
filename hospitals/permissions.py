from rest_framework import permissions

class IsOperatorReadOnly(permissions.BasePermission):
    """
    Operator has strictly read-only access to endpoints.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if request.user.role == 'operator':
            return request.method in permissions.SAFE_METHODS
            
        return True # Handled by other permissions if not operator

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role == 'operator':
            return request.method in permissions.SAFE_METHODS
            
        return True

class IsHospitalManagerOwnHospital(permissions.BasePermission):
    """
    Hospital Manager can read, and can write ONLY to their assigned hospital.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role == 'hospital_manager':
            # Allow safe methods globally, object-level handles specific reads if needed
            return True
            
        return True

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role == 'hospital_manager':
            # For safe methods, let them read anything (or restrict? Prompt: "hospital_manager: still returns all in the raw queryset but see RBAC scoping below... enforced in the response")
            # Wait, prompt says: "hospital_manager: write access, but the queryset/serializer must filter and validate against request.user.hospital_id server-side"
            # And "operator: read access to all hospitals"
            # It seems hospital_manager can read all hospitals, but can only write to their own.
            
            if request.method in permissions.SAFE_METHODS:
                return True
                
            # It's a write method (PUT/PATCH). obj is a Hospital.
            # If the view acts on something else, we would need to check obj type.
            from .models import Hospital
            if getattr(obj, '_meta', None) and obj._meta.model == Hospital:
                return obj.id == request.user.hospital_id
                
            # If acting on a Department or Equipment
            if hasattr(obj, 'hospital'):
                return obj.hospital.id == request.user.hospital_id
                
            return False
            
        return True

class CombinedHospitalPermission(permissions.BasePermission):
    """
    Combines the constraints.
    """
    def has_permission(self, request, view):
        # We assume IsAuthenticated is enforced view-level
        if request.user.role == 'operator':
            return request.method in permissions.SAFE_METHODS
        if request.user.role == 'hospital_manager':
            return True # Details handled in object perms
        return False # Admin or unknown not allowed here

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'operator':
            return request.method in permissions.SAFE_METHODS
            
        if request.user.role == 'hospital_manager':
            if request.method in permissions.SAFE_METHODS:
                return True
                
            from .models import Hospital
            if getattr(obj, '_meta', None) and obj._meta.model == Hospital:
                return obj.id == request.user.hospital_id
                
            if hasattr(obj, 'hospital'):
                return obj.hospital.id == request.user.hospital_id
                
            return False
            
        return False
