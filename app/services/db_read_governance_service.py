from __future__ import annotations

import re
from typing import Any

from app.errors import AppError
from app.services.purview_visibility_service import (
    ALLOW_RESULTS,
    PurviewVisibilityService,
    VisibilityDecision,
)
from app.services.sql_resource_parser import SQLReadResourceSet, SQLResourceParser


class DBReadGovernanceService:
    def __init__(self, parser: SQLResourceParser, purview_service: PurviewVisibilityService) -> None:
        self._parser = parser
        self._purview_service = purview_service

    def authorize(self, sql: str, user_principal_name: str) -> tuple[SQLReadResourceSet, list[VisibilityDecision]]:
        resources = self._parser.parse(sql)
        decisions: list[VisibilityDecision] = []
        for table in resources.tables:
            decisions.append(
                self._purview_service.query_visibility(
                    resource_type="table",
                    qualified_name=table.qualified_name,
                    user_principal_name=user_principal_name,
                )
            )
        for column in resources.columns:
            decisions.append(
                self._purview_service.query_visibility(
                    resource_type="column",
                    qualified_name=column.qualified_name,
                    user_principal_name=user_principal_name,
                )
            )
        denied = [decision.qualified_name for decision in decisions if decision.result == "DENY"]
        if denied:
            raise AppError(
                "Current user is not allowed to read data:" + ",".join(sorted(denied)),
                403,
            )
        return resources, decisions

    def apply_masks(
        self,
        rows: list[dict[str, Any]],
        resources: SQLReadResourceSet,
        decisions: list[VisibilityDecision],
    ) -> list[dict[str, Any]]:
        if not rows:
            return rows
        table_masks = [decision.qualified_name for decision in decisions if decision.resource_type == "table" and decision.result == "MASK"]
        column_masks = {
            decision.qualified_name
            for decision in decisions
            if decision.resource_type == "column" and decision.result == "MASK"
        }
        if not table_masks and not column_masks:
            return rows
        if any(decision.result not in ALLOW_RESULTS | {"MASK"} for decision in decisions):
            return rows

        masked_rows: list[dict[str, Any]] = []
        for row in rows:
            masked = dict(row)
            for column_name, value in row.items():
                if value is None:
                    continue
                if table_masks and not _is_id_like(column_name):
                    masked[column_name] = self._purview_service.mask(
                        qualified_name=table_masks[0],
                        mask_input=value,
                    )
                    continue
                source_names = set(resources.result_column_sources.get(_canonical(column_name), []))
                if source_names & column_masks:
                    masked[column_name] = self._purview_service.mask(
                        qualified_name=sorted(source_names & column_masks)[0],
                        mask_input=value,
                    )
            masked_rows.append(masked)
        return masked_rows


def _is_id_like(column_name: str) -> bool:
    normalized = str(column_name).strip()
    return normalized.upper() == "ID" or normalized.upper().endswith("ID") or bool(re.search(r"(?i)(^|[-_])ID$", normalized))


def _canonical(value: str) -> str:
    return str(value).lower().replace(" ", "").replace("_", "").replace("-", "")
