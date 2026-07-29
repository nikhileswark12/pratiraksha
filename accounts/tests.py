from django.test import TestCase

from .models import User
class UserRoleTestCase(TestCase):
    def test_user_creation(self):
        """Test that the user can be created with a specific role."""
        user = User.objects.create_user(email="test@operator.com", password="Password1!", name="Test Operator", role="operator")
        self.assertEqual(user.role, "operator")
        self.assertIsNone(user.hospital)
