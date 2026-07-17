from django.test import TestCase
from accounts.models import User

class UserRoleTestCase(TestCase):
    def test_user_creation(self):
        """Test that the user can be created with a specific role."""
        user = User.objects.create(username="testoperator", role="operator")
        self.assertEqual(user.role, "operator")
        self.assertIsNone(user.hospital)
