from __future__ import annotations

from app.data.repositories.mock_data import PRODUCTS
from app.data.sql_client import SqlClient


class ProductRepository:
    def __init__(self, sql_client: SqlClient | None) -> None:
        self._sql_client = sql_client

    def list_bootstrap_products(self) -> list[dict]:
        if self._sql_client is None:
            return PRODUCTS
        sql = """
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
        SELECT TOP 10 product_id, product_name, category_name, model_name, description
        FROM RankedProducts WHERE rn = 1 ORDER BY category_rank;
        """
        return self._sql_client.query(sql)
