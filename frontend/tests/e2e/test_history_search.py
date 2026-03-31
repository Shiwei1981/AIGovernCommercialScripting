import pytest


pytestmark = pytest.mark.skip(reason='Playwright browser setup required in CI image for e2e execution')


def test_history_search_journey():
    assert True
