"""Contract tests that keep the API in sync with docs/endpoints.md.

Each documented endpoint is one parametrized case. Implemented endpoints must
resolve and accept the documented HTTP method. Endpoints that are not built yet
are marked ``xfail(strict=True)`` so the suite stays green while they are still
missing, and turns red the moment they start resolving (forcing the marker to
be removed together with real behavioural tests).
"""

import pytest
from django.urls import Resolver404, resolve

XFAIL_MISSING = 'Endpoint noch nicht implementiert (siehe docs/endpoints.md).'


def _missing():
    """Mark a documented but unimplemented endpoint as an expected failure."""
    return pytest.mark.xfail(
        reason=XFAIL_MISSING,
        strict=True,
        raises=(AssertionError, Resolver404),
    )


def _allowed_methods(match):
    """Return the uppercase HTTP methods the resolved view actually handles."""
    actions = getattr(match.func, 'actions', None)
    if actions is not None:
        return {method.upper() for method in actions}

    view_cls = getattr(match.func, 'cls', None)
    if view_cls is not None:
        return {
            method.upper()
            for method in view_cls.http_method_names
            if hasattr(view_cls, method)
        }

    return set()


DOCUMENTED_ENDPOINTS = [
    pytest.param('POST', '/api/registration/', id='POST /api/registration/'),
    pytest.param('POST', '/api/login/', id='POST /api/login/'),
    pytest.param('GET', '/api/profile/1/', id='GET /api/profile/{pk}/'),
    pytest.param('PATCH', '/api/profile/1/', id='PATCH /api/profile/{pk}/'),
    pytest.param('GET', '/api/profiles/business/', id='GET /api/profiles/business/'),
    pytest.param('GET', '/api/profiles/customer/', id='GET /api/profiles/customer/'),
    pytest.param('GET', '/api/offers/', id='GET /api/offers/'),
    pytest.param('POST', '/api/offers/', id='POST /api/offers/'),
    pytest.param('GET', '/api/offers/1/', id='GET /api/offers/{id}/'),
    pytest.param('PATCH', '/api/offers/1/', id='PATCH /api/offers/{id}/'),
    pytest.param('DELETE', '/api/offers/1/', id='DELETE /api/offers/{id}/'),
    pytest.param('GET', '/api/offerdetails/1/', id='GET /api/offerdetails/{id}/'),
    pytest.param('GET', '/api/orders/', id='GET /api/orders/'),
    pytest.param('POST', '/api/orders/', id='POST /api/orders/'),
    pytest.param('PATCH', '/api/orders/1/', id='PATCH /api/orders/{id}/'),
    pytest.param('DELETE', '/api/orders/1/', id='DELETE /api/orders/{id}/'),
    pytest.param(
        'GET',
        '/api/order-count/1/',
        id='GET /api/order-count/{business_user_id}/',
    ),
    pytest.param(
        'GET',
        '/api/completed-order-count/1/',
        id='GET /api/completed-order-count/{business_user_id}/',
    ),
    pytest.param('GET', '/api/reviews/', marks=_missing(), id='GET /api/reviews/'),
    pytest.param('POST', '/api/reviews/', marks=_missing(), id='POST /api/reviews/'),
    pytest.param(
        'PATCH', '/api/reviews/1/', marks=_missing(), id='PATCH /api/reviews/{id}/'
    ),
    pytest.param(
        'DELETE', '/api/reviews/1/', marks=_missing(), id='DELETE /api/reviews/{id}/'
    ),
    pytest.param('GET', '/api/base-info/', marks=_missing(), id='GET /api/base-info/'),
]


@pytest.mark.parametrize('method, path', DOCUMENTED_ENDPOINTS)
def test_documented_endpoint_is_available(method, path):
    match = resolve(path)
    allowed = _allowed_methods(match)
    assert method in allowed, (
        f'{method} {path} wird nicht akzeptiert. '
        f'Vorhandene Methoden: {sorted(allowed)}.'
    )
