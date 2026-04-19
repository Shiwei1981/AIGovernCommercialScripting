import pytest

from app.errors import AppError
from app.services.nl2sql_service import validate_select_only


def test_guard_allows_select():
    validate_select_only("SELECT * FROM Customer")


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM Customer",
        "UPDATE Customer SET Name='x'",
        "SELECT * FROM C; DROP TABLE X",
    ],
)
def test_guard_rejects_non_readonly(sql):
    with pytest.raises(AppError):
        validate_select_only(sql)
