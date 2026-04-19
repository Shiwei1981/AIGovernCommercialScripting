from __future__ import annotations

from app.data.repositories.product_repository import ProductRepository


class ProductBootstrapService:
    def __init__(self, repository: ProductRepository):
        self._repository = repository

    def get_bootstrap_products(self) -> list[dict]:
        return self._repository.list_bootstrap_products()
