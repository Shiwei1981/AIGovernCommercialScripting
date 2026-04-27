from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings
from app.errors import AppError

ALLOW_RESULTS = {"ALLOW", "INDETERMINATE", "NOT_APPLICABLE"}
VALID_RESULTS = ALLOW_RESULTS | {"DENY", "MASK"}
ID_BYPASS_RESULT = "NOT_APPLICABLE"


@dataclass(frozen=True)
class VisibilityDecision:
    resource_type: str
    qualified_name: str
    result: str


class PurviewVisibilityService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def query_visibility(
        self,
        *,
        resource_type: str,
        qualified_name: str,
        user_principal_name: str,
    ) -> VisibilityDecision:
        if _qualified_name_ends_with_id(qualified_name):
            return VisibilityDecision(resource_type=resource_type, qualified_name=qualified_name, result=ID_BYPASS_RESULT)
        payload = {
            "QualifiedName": qualified_name,
            "UserPrincipalName": user_principal_name,
        }
        try:
            response = httpx.post(self._settings.queryvisibility_api_url, json=payload, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AppError(f"QueryVisibility failed for {qualified_name}.", 502) from exc
        result = _extract_result(response)
        if result not in VALID_RESULTS:
            raise AppError(f"QueryVisibility returned unsupported result for {qualified_name}: {result}", 502)
        return VisibilityDecision(resource_type=resource_type, qualified_name=qualified_name, result=result)

    def mask(self, *, qualified_name: str, mask_input: Any) -> str:
        payload = {"QualifiedName": qualified_name, "MaskInput": "" if mask_input is None else str(mask_input)}
        try:
            response = httpx.post(self._settings.mask_api_url, json=payload, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AppError(f"Mask failed for {qualified_name}.", 502) from exc
        return _extract_mask(response)


def _extract_result(response: httpx.Response) -> str:
    text = response.text.strip().strip('"')
    try:
        payload = response.json()
    except ValueError:
        payload = text
    if isinstance(payload, str):
        return payload.strip().upper()
    if isinstance(payload, dict):
        for key in ("result_string", "result", "decision", "visibility"):
            value = payload.get(key) or payload.get(key.upper()) or payload.get(key.title())
            if value is not None:
                return str(value).strip().upper()
    return text.upper()


def _qualified_name_ends_with_id(qualified_name: str) -> bool:
    return qualified_name.strip().upper().endswith("ID")


def _extract_mask(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("result_string", "masked_value", "maskedString", "MaskOutput", "result"):
            value = payload.get(key)
            if value is not None:
                return str(value)
    return response.text
