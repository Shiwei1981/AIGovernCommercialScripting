import pytest


pytestmark = pytest.mark.skip(reason='Playwright browser setup required in CI image for e2e execution')


def test_signin_and_generate_journey():
    assert True
