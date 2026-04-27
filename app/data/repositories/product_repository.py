from __future__ import annotations

from app.data.repositories.mock_data import PRODUCTS
from app.data.sql_client import SqlClient

DEFAULT_PRODUCT_PAGE_SIZE = 4
HARD_MAX_PRODUCT_PAGE_SIZE = 20
LEGACY_PRODUCT_LIMIT = 10


class ProductRepository:
    def __init__(self, sql_client: SqlClient | None) -> None:
        self._sql_client = sql_client

    def list_products_page(
        self,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PRODUCT_PAGE_SIZE,
        user_principal_name: str | None = None,
    ) -> dict:
        normalized_page = _normalize_page(page)
        normalized_page_size = _normalize_page_size(page_size)
        if self._sql_client is None:
            total_count = len(PRODUCTS)
            normalized_page = _clamp_page_to_total(
                normalized_page,
                normalized_page_size,
                total_count,
            )
            offset = (normalized_page - 1) * normalized_page_size
            items = PRODUCTS[offset : offset + normalized_page_size]
            return _product_page_response(items, normalized_page, normalized_page_size, total_count)

        offset = (normalized_page - 1) * normalized_page_size
        rows = self._sql_client.query(
            _ranked_product_page_sql(),
            (offset, normalized_page_size),
            user_principal_name=user_principal_name,
        )
        total_count = int(rows[0]["total_count"]) if rows else 0
        return _product_page_response(
            _strip_total_count(rows),
            normalized_page,
            normalized_page_size,
            total_count,
        )

    def list_bootstrap_products(self, user_principal_name: str | None = None) -> list[dict]:
        return self.list_products_page(
            page=1,
            page_size=LEGACY_PRODUCT_LIMIT,
            user_principal_name=user_principal_name,
        )["items"]

    def get_product_by_id(
        self,
        product_id: int,
        user_principal_name: str | None = None,
    ) -> dict | None:
        if self._sql_client is None:
            return next((product for product in PRODUCTS if int(product["product_id"]) == product_id), None)
        rows = self._sql_client.query(
            """
            SELECT TOP 1
                p.ProductID AS product_id,
                p.Name AS product_name,
                pc.Name AS category_name,
                pm.Name AS model_name,
                pd.Description AS description
            FROM SalesLT.Product p
            JOIN SalesLT.ProductCategory pc ON p.ProductCategoryID = pc.ProductCategoryID
            LEFT JOIN SalesLT.ProductModel pm ON p.ProductModelID = pm.ProductModelID
            LEFT JOIN SalesLT.ProductModelProductDescription pmpd
                ON pm.ProductModelID = pmpd.ProductModelID AND pmpd.Culture = 'en'
            LEFT JOIN SalesLT.ProductDescription pd ON pmpd.ProductDescriptionID = pd.ProductDescriptionID
            WHERE p.ProductID = ?
            ORDER BY p.ProductID
            """,
            (product_id,),
            user_principal_name=user_principal_name,
        )
        return rows[0] if rows else None


def _ranked_product_base_cte() -> str:
    return """
    WITH RankedProducts AS (
        SELECT
            p.ProductID AS product_id,
            p.Name AS product_name,
            pc.Name AS category_name,
            pm.Name AS model_name,
            pd.Description AS description,
            ROW_NUMBER() OVER(PARTITION BY pc.ProductCategoryID ORDER BY p.ProductID) AS rn,
            DENSE_RANK() OVER(ORDER BY pc.ProductCategoryID) AS category_rank
        FROM SalesLT.Product p
        JOIN SalesLT.ProductCategory pc ON p.ProductCategoryID = pc.ProductCategoryID
        LEFT JOIN SalesLT.ProductModel pm ON p.ProductModelID = pm.ProductModelID
        LEFT JOIN SalesLT.ProductModelProductDescription pmpd
            ON pm.ProductModelID = pmpd.ProductModelID AND pmpd.Culture = 'en'
        LEFT JOIN SalesLT.ProductDescription pd ON pmpd.ProductDescriptionID = pd.ProductDescriptionID
    )
    """


def _ranked_product_page_sql() -> str:
    return (
        _ranked_product_base_cte()
        + """
        SELECT
            product_id,
            product_name,
            category_name,
            model_name,
            description,
            COUNT(1) OVER() AS total_count
        FROM RankedProducts
        WHERE rn = 1
        ORDER BY category_rank, product_id
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
    )


def _strip_total_count(rows: list[dict]) -> list[dict]:
    return [{key: value for key, value in row.items() if key != "total_count"} for row in rows]


def _product_page_response(items: list[dict], page: int, page_size: int, total_count: int) -> dict:
    total_pages = (total_count + page_size - 1) // page_size if total_count else 0
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
    }


def _normalize_page(page: int) -> int:
    try:
        parsed = int(page)
    except (TypeError, ValueError):
        parsed = 1
    return max(1, parsed)


def _normalize_page_size(page_size: int) -> int:
    try:
        parsed = int(page_size)
    except (TypeError, ValueError):
        parsed = DEFAULT_PRODUCT_PAGE_SIZE
    return max(1, min(parsed, HARD_MAX_PRODUCT_PAGE_SIZE))


def _clamp_page_to_total(page: int, page_size: int, total_count: int) -> int:
    if total_count <= 0:
        return 1
    total_pages = (total_count + page_size - 1) // page_size
    return min(page, total_pages)
