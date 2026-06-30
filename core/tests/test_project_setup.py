from django.conf import settings


def test_django_settings_are_configured():
    assert settings.ROOT_URLCONF == 'core.urls'
    assert 'rest_framework' in settings.INSTALLED_APPS
    assert 'rest_framework.authtoken' in settings.INSTALLED_APPS
