from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import Settings
from app.data.repositories.ai_generation_log_repository import AIGenerationLogRepository
from app.data.repositories.customer_repository import CustomerRepository
from app.data.repositories.product_repository import ProductRepository


@dataclass
class AppState:
    settings: Settings
    product_repository: ProductRepository
    customer_repository: CustomerRepository
    ai_log_repository: AIGenerationLogRepository
    sessions: dict[str, dict[str, Any]] = field(default_factory=dict)
