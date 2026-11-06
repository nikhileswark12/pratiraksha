import pytest
from django.conf import settings
from django.test import override_settings


@pytest.fixture(autouse=True)
def disable_throttling_during_tests():
    rest_framework = dict(settings.REST_FRAMEWORK)
    rates = dict(rest_framework.get("DEFAULT_THROTTLE_RATES", {}))
    rates["anon"] = "10000/hour"
    rates["user"] = "10000/hour"
    rest_framework["DEFAULT_THROTTLE_RATES"] = rates
    with override_settings(REST_FRAMEWORK=rest_framework):
        yield
