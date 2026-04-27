from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import sqlglot
from sqlglot import expressions as exp

from app.config import Settings
from app.errors import AppError

SQL_RESOURCE_PARSE_ERROR = "Unable to determine all tables and columns referenced by the query."
READONLY_VIOLATION_ERROR = "Generated SQL violates read-only policy."
DEFAULT_SCHEMA = "SalesLT"


@dataclass(frozen=True)
class SQLTableResource:
    schema_name: str
    table_name: str
    qualified_name: str


@dataclass(frozen=True)
class SQLColumnResource:
    schema_name: str
    table_name: str
    column_name: str
    qualified_name: str


@dataclass
class SQLReadResourceSet:
    tables: list[SQLTableResource]
    columns: list[SQLColumnResource]
    result_column_sources: dict[str, list[str]] = field(default_factory=dict)


def build_qualified_name(
    settings: Settings,
    schema_name: str,
    table_name: str,
    column_name: str | None = None,
) -> str:
    server_host = _qualified_sql_server_host(settings.sql_server)
    schema = _normalize_identifier_part(schema_name)
    table = _normalize_identifier_part(table_name)
    base = (
        f"mssql://{server_host}/"
        f"{settings.sql_database}/{schema}/{table}"
    )
    if column_name is None:
        return base
    return f"{base}#{_normalize_identifier_part(column_name)}"


class SQLResourceParser:
    def __init__(
        self,
        settings: Settings,
        column_resolver: Callable[[str, str], list[str]],
    ) -> None:
        self._settings = settings
        self._column_resolver = column_resolver

    def parse(self, sql: str) -> SQLReadResourceSet:
        expression = _parse_single_select(sql)
        table_by_alias = self._collect_tables(expression)
        if not table_by_alias:
            raise AppError(SQL_RESOURCE_PARSE_ERROR, 422)

        table_resources = _unique_tables(table_by_alias.values())
        metadata = self._load_metadata(table_resources)
        derived_names = _derived_column_names(expression)
        column_resources = self._collect_columns(expression, table_by_alias, metadata, derived_names)
        result_sources = self._collect_result_sources(expression, table_by_alias, metadata, derived_names)
        return SQLReadResourceSet(
            tables=table_resources,
            columns=column_resources,
            result_column_sources=result_sources,
        )

    def _collect_tables(self, expression: exp.Expression) -> dict[str, SQLTableResource]:
        cte_names = {str(cte.alias).lower() for cte in expression.find_all(exp.CTE) if cte.alias}
        tables: dict[str, SQLTableResource] = {}
        for table in expression.find_all(exp.Table):
            raw_table_name = _normalize_identifier_part(str(table.name))
            raw_schema_name = _normalize_identifier_part(str(table.db or DEFAULT_SCHEMA))
            schema_name, table_name = _normalize_table_parts(raw_schema_name, raw_table_name)
            if not str(table.db or "") and table_name.lower() in cte_names:
                continue
            resource = SQLTableResource(
                schema_name=schema_name,
                table_name=table_name,
                qualified_name=build_qualified_name(self._settings, schema_name, table_name),
            )
            aliases = {table_name.lower(), f"{schema_name}.{table_name}".lower()}
            if table.alias:
                aliases.add(str(table.alias).lower())
            for alias in aliases:
                tables[alias] = resource
        return tables

    def _load_metadata(self, table_resources: list[SQLTableResource]) -> dict[tuple[str, str], list[str]]:
        metadata: dict[tuple[str, str], list[str]] = {}
        for table in table_resources:
            columns = self._column_resolver(table.schema_name, table.table_name)
            if not columns:
                raise AppError(SQL_RESOURCE_PARSE_ERROR, 422)
            metadata[(table.schema_name.lower(), table.table_name.lower())] = columns
        return metadata

    def _collect_columns(
        self,
        expression: exp.Expression,
        table_by_alias: dict[str, SQLTableResource],
        metadata: dict[tuple[str, str], list[str]],
        derived_names: set[str],
    ) -> list[SQLColumnResource]:
        resources: dict[tuple[str, str, str], SQLColumnResource] = {}
        for table in _unique_tables(table_by_alias.values()):
            for column_name in _expanded_star_columns(expression, table, table_by_alias, metadata):
                resource = _column_resource(self._settings, table, column_name)
                resources[(table.schema_name.lower(), table.table_name.lower(), column_name.lower())] = resource

        for column in expression.find_all(exp.Column):
            column_name = str(column.name)
            if column_name == "*":
                continue
            table = _resolve_column_table(column, table_by_alias, metadata, derived_names)
            if table is None:
                continue
            resource = _column_resource(self._settings, table, _actual_column_name(table, column_name, metadata))
            resources[(table.schema_name.lower(), table.table_name.lower(), column_name.lower())] = resource
        return list(resources.values())

    def _collect_result_sources(
        self,
        expression: exp.Expression,
        table_by_alias: dict[str, SQLTableResource],
        metadata: dict[tuple[str, str], list[str]],
        derived_names: set[str],
    ) -> dict[str, list[str]]:
        result_sources: dict[str, list[str]] = {}
        if not isinstance(expression, exp.Select):
            return result_sources
        for projection in expression.expressions:
            for table in _projection_star_tables(projection, table_by_alias):
                for column_name in _metadata_columns(table, metadata):
                    result_sources.setdefault(_canonical(column_name), []).append(
                        _column_resource(self._settings, table, column_name).qualified_name
                    )
            if _is_star_projection(projection):
                continue
            alias = projection.alias_or_name
            if not alias:
                continue
            source_names: list[str] = []
            for column in projection.find_all(exp.Column):
                if str(column.name) == "*":
                    continue
                table = _resolve_column_table(column, table_by_alias, metadata, derived_names)
                if table is None:
                    continue
                source_names.append(
                    _column_resource(
                        self._settings,
                        table,
                        _actual_column_name(table, str(column.name), metadata),
                    ).qualified_name
                )
            if source_names:
                result_sources[_canonical(alias)] = sorted(set(source_names))
        return {key: sorted(set(values)) for key, values in result_sources.items()}


def _parse_single_select(sql: str) -> exp.Expression:
    try:
        expressions = sqlglot.parse(sql.strip().rstrip(";"), read="tsql")
    except sqlglot.errors.ParseError as exc:
        raise AppError(SQL_RESOURCE_PARSE_ERROR, 422) from exc
    if len(expressions) != 1:
        raise AppError(READONLY_VIOLATION_ERROR, 400)
    expression = expressions[0]
    if not isinstance(expression, exp.Select):
        raise AppError(READONLY_VIOLATION_ERROR, 400)
    return expression


def _unique_tables(tables: Any) -> list[SQLTableResource]:
    unique: dict[tuple[str, str], SQLTableResource] = {}
    for table in tables:
        unique[(table.schema_name.lower(), table.table_name.lower())] = table
    return list(unique.values())


def _column_resource(settings: Settings, table: SQLTableResource, column_name: str) -> SQLColumnResource:
    return SQLColumnResource(
        schema_name=table.schema_name,
        table_name=table.table_name,
        column_name=column_name,
        qualified_name=build_qualified_name(settings, table.schema_name, table.table_name, column_name),
    )


def _metadata_columns(
    table: SQLTableResource,
    metadata: dict[tuple[str, str], list[str]],
) -> list[str]:
    return metadata[(table.schema_name.lower(), table.table_name.lower())]


def _actual_column_name(
    table: SQLTableResource,
    column_name: str,
    metadata: dict[tuple[str, str], list[str]],
) -> str:
    for actual in _metadata_columns(table, metadata):
        if actual.lower() == column_name.lower():
            return actual
    return column_name


def _expanded_star_columns(
    expression: exp.Expression,
    table: SQLTableResource,
    table_by_alias: dict[str, SQLTableResource],
    metadata: dict[tuple[str, str], list[str]],
) -> list[str]:
    columns: list[str] = []
    for column in expression.find_all(exp.Column):
        if str(column.name) != "*":
            continue
        table_name = str(column.table or "").lower()
        if table_name:
            resolved = table_by_alias.get(table_name)
            if resolved == table:
                columns.extend(_metadata_columns(table, metadata))
            continue
        columns.extend(_metadata_columns(table, metadata))
    for star in expression.find_all(exp.Star):
        if isinstance(star.parent, exp.Column):
            continue
        columns.extend(_metadata_columns(table, metadata))
    return columns


def _is_star_projection(projection: exp.Expression) -> bool:
    return isinstance(projection, exp.Star) or (
        isinstance(projection, exp.Column) and str(projection.name) == "*"
    )


def _projection_star_tables(
    projection: exp.Expression,
    table_by_alias: dict[str, SQLTableResource],
) -> list[SQLTableResource]:
    if not _is_star_projection(projection):
        return []
    if isinstance(projection, exp.Column) and projection.table:
        table = table_by_alias.get(str(projection.table).lower())
        if table is None:
            raise AppError(SQL_RESOURCE_PARSE_ERROR, 422)
        return [table]
    return _unique_tables(table_by_alias.values())


def _resolve_column_table(
    column: exp.Column,
    table_by_alias: dict[str, SQLTableResource],
    metadata: dict[tuple[str, str], list[str]],
    derived_names: set[str],
) -> SQLTableResource | None:
    table_key = str(column.table or "").lower()
    column_name = str(column.name)
    if table_key:
        table = table_by_alias.get(table_key)
        if table is None:
            if column_name.lower() in derived_names:
                return None
            raise AppError(SQL_RESOURCE_PARSE_ERROR, 422)
        return table
    matches: list[SQLTableResource] = []
    for table in _unique_tables(table_by_alias.values()):
        columns = {name.lower() for name in _metadata_columns(table, metadata)}
        if column_name.lower() in columns:
            matches.append(table)
    if len(matches) == 1:
        return matches[0]
    if column_name.lower() in derived_names:
        return None
    if len(_unique_tables(table_by_alias.values())) == 1 and not matches:
        return _unique_tables(table_by_alias.values())[0]
    raise AppError(SQL_RESOURCE_PARSE_ERROR, 422)


def _derived_column_names(expression: exp.Expression) -> set[str]:
    names: set[str] = set()
    for projection in getattr(expression, "expressions", []):
        if projection.alias:
            names.add(str(projection.alias).lower())
    for cte in expression.find_all(exp.CTE):
        for select in cte.find_all(exp.Select):
            for projection in select.expressions:
                alias = projection.alias_or_name
                if alias:
                    names.add(str(alias).lower())
    for subquery in expression.find_all(exp.Subquery):
        for select in subquery.find_all(exp.Select):
            if select is expression:
                continue
            for projection in select.expressions:
                alias = projection.alias_or_name
                if alias:
                    names.add(str(alias).lower())
    return names


def _canonical(value: str) -> str:
    return str(value).lower().replace(" ", "").replace("_", "").replace("-", "")


def _qualified_sql_server_host(sql_server: str) -> str:
    server = sql_server.strip().removeprefix("tcp:")
    server = re.split(r"[,/:]", server, maxsplit=1)[0].strip()
    suffix = ".database.windows.net"
    if server.lower().endswith(suffix):
        return server
    return f"{server}{suffix}"


def _normalize_identifier_part(value: str) -> str:
    normalized = str(value).strip()
    while len(normalized) >= 2 and (
        (normalized[0] == "[" and normalized[-1] == "]")
        or (normalized[0] == '"' and normalized[-1] == '"')
    ):
        normalized = normalized[1:-1].strip()
    return normalized


def _normalize_table_parts(schema_name: str, table_name: str) -> tuple[str, str]:
    schema = _normalize_identifier_part(schema_name) or DEFAULT_SCHEMA
    table = _normalize_identifier_part(table_name)
    parts = [_normalize_identifier_part(part) for part in table.split(".") if part]
    if len(parts) >= 2:
        schema = parts[-2]
        table = parts[-1]
    return schema, table
