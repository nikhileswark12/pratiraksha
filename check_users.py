import sys
from django.contrib.auth import get_user_model

User = get_user_model()

operator = User.objects.filter(email='operator@example.com').first()
hm1 = User.objects.filter(email='hm1@test.com').first()

if not operator:
    print("Operator user not found!")
else:
    print(f"Operator User: {operator.email}, Role: {getattr(operator, 'role', 'Unknown')}")
    print(f"Password hash: {operator.password[:30]}...")
    print(f"check_password('operatorpass'): {operator.check_password('operatorpass')}")

if not hm1:
    print("HM1 user not found!")
else:
    print(f"HM1 User: {hm1.email}, Role: {getattr(hm1, 'role', 'Unknown')}")
    print(f"Password hash: {hm1.password[:30]}...")
    print(f"check_password('hm1pass'): {hm1.check_password('hm1pass')}")

if operator and not operator.check_password('operatorpass'):
    print("Resetting operator password...")
    operator.set_password('operatorpass')
    operator.save()
    print(f"After reset, check_password('operatorpass'): {operator.check_password('operatorpass')}")

if hm1 and not hm1.check_password('hm1pass'):
    print("Resetting hm1 password...")
    hm1.set_password('hm1pass')
    hm1.save()
    print(f"After reset, check_password('hm1pass'): {hm1.check_password('hm1pass')}")
