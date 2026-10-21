from django.test import TestCase
from .serializers import RegisterSerializer

from .models import User
class UserRoleTestCase(TestCase):
    def test_user_creation(self):
        """Test that the user can be created with a specific role."""
        user = User.objects.create_user(email="test@operator.com", password="Password1!", name="Test Operator", role="operator")
        self.assertEqual(user.role, "operator")
        self.assertIsNone(user.hospital)


class PublicRegistrationRoleTests(TestCase):
    def test_hospital_manager_cannot_self_register(self):
        serializer = RegisterSerializer(data={
            "name": "Unauthorized Manager",
            "email": "manager-self-register@test.com",
            "password": "StrongPass1!",
            "role": "hospital_manager",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("role", serializer.errors)
