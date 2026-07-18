from django.contrib.auth.hashers import BCryptSHA256PasswordHasher

class StrictBCryptPasswordHasher(BCryptSHA256PasswordHasher):
    """
    Subclass of BCryptSHA256PasswordHasher that enforces exactly 10 rounds
    as specified in the tech spec for Pratiraksha v3.1.
    """
    rounds = 10
