from django.conf import settings

from core.urls import urlpatterns


def test_admin_url_is_registered():
    assert any(str(pattern.pattern) == 'admin/' for pattern in urlpatterns)


def test_django_settings_are_configured():
    assert settings.ROOT_URLCONF == 'core.urls'
    assert 'rest_framework' in settings.INSTALLED_APPS
    assert 'rest_framework.authtoken' in settings.INSTALLED_APPS
