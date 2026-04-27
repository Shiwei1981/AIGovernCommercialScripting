from __future__ import annotations

from app.data.repositories.product_repository import ProductRepository


class ProductBootstrapService:
    def __init__(self, repository: ProductRepository):
        self._repository = repository

    def get_products_page(
        self,
        *,
        page: int = 1,
        page_size: int = 4,
        user_principal_name: str | None = None,
    ) -> dict:
        return self._repository.list_products_page(
            page=page,
            page_size=page_size,
            user_principal_name=user_principal_name,
        )

    def get_bootstrap_products(self, user_principal_name: str | None = None) -> list[dict]:
        return self._repository.list_bootstrap_products(user_principal_name=user_principal_name)

    def get_product_by_id(
        self,
        product_id: int,
        user_principal_name: str | None = None,
    ) -> dict | None:
        return self._repository.get_product_by_id(
            product_id=product_id,
            user_principal_name=user_principal_name,
        )
