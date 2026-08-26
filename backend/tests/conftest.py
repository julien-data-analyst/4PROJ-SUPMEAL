import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Resets DRF's throttle cache (see ``ScopedRateThrottle``, keyed by
    scope + caller IP) before and after every test.

    Without this, the default ``LocMemCache`` used for throttling persists
    for the whole pytest process - tests hitting the same rate-limited
    endpoint (e.g. ``/api/users/login/``) from the same test-client IP would
    otherwise accumulate hits across unrelated tests and start failing with
    429s depending on execution order.
    """
    cache.clear()
    yield
    cache.clear()
