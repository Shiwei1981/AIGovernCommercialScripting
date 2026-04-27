from __future__ import annotations

from app.data.repositories.product_repository import ProductRepository


class FakeSqlClient:
    def __init__(self) -> None:
        self.queries: list[tuple[str, tuple]] = []

    def query(self, sql: str, params=(), **_kwargs):  # noqa: ANN001
        self.queries.append((sql, params))
        return [
            {
                "product_id": 1,
                "product_name": "Road Tire",
                "category_name": "Tires",
                "model_name": "Road",
                "description": "Demo",
                "total_count": 9,
            }
        ]


def test_list_products_page_uses_single_query_with_total_count_window():
    sql_client = FakeSqlClient()
    repo = ProductRepository(sql_client)

    page = repo.list_products_page(page=2, page_size=4, user_principal_name="user@example.com")

    assert len(sql_client.queries) == 1
    sql, params = sql_client.queries[0]
    assert "COUNT(1) OVER() AS total_count" in sql
    assert "SELECT COUNT(1) AS total_count" not in sql
    assert params == (4, 4)
    assert page["page"] == 2
    assert page["page_size"] == 4
    assert page["total_count"] == 9
    assert page["total_pages"] == 3
    assert "total_count" not in page["items"][0]
