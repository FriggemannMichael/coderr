import importlib.util

from django.conf import settings
from django.urls import URLResolver

from core.urls import urlpatterns

EXPECTED_PROJECT_APPS = [
    'auth_app',
    'profiles_app',
    'offers_app',
    'orders_app',
    'reviews_app',
]

EXPECTED_API_URL_MODULES = [
    f'{app_name}.api.urls' for app_name in EXPECTED_PROJECT_APPS
]


def test_project_apps_are_installed():
    for app_name in EXPECTED_PROJECT_APPS:
        assert app_name in settings.INSTALLED_APPS


def test_project_apps_expose_api_url_modules():
    for app_name in EXPECTED_PROJECT_APPS:
        assert importlib.util.find_spec(f'{app_name}.api.urls') is not None


def test_core_urls_include_project_api_modules():
    included_modules = set()

    for pattern in urlpatterns:
        if not isinstance(pattern, URLResolver):
            continue

        urlconf_name = pattern.urlconf_name
        if isinstance(urlconf_name, str):
            included_modules.add(urlconf_name)
        elif hasattr(urlconf_name, '__name__'):
            included_modules.add(urlconf_name.__name__)

    for module_name in EXPECTED_API_URL_MODULES:
        assert module_name in included_modules
