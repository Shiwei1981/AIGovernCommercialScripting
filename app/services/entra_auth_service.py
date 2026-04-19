from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from fastapi import Request

from app.config import Settings
from app.errors import AppError


def _decode_jwt_payload(token: str) -> dict:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload.encode("utf-8")).decode("utf-8"))


class EntraAuthService:
    def __init__(self, settings: Settings, session_store: dict[str, dict]):
        self._settings = settings
        self._sessions = session_store

    def _authority_base_url(self) -> str:
        authority = self._settings.oidc_authority_url.strip().rstrip("/")
        for suffix in ("/oauth2/v2.0", "/v2.0"):
            if authority.endswith(suffix):
                return authority[: -len(suffix)]
        return authority

    def _oauth_endpoint(self, endpoint: str) -> str:
        return f"{self._authority_base_url()}/oauth2/v2.0/{endpoint}"

    def login_redirect_url(self) -> str:
        state = str(uuid4())
        query = urlencode(
            {
                "client_id": self._settings.azure_client_id,
                "response_type": "code",
                "redirect_uri": self._settings.oidc_callback_url,
                "response_mode": "query",
                "scope": "openid profile email",
                "state": state,
            }
        )
        return f"{self._oauth_endpoint('authorize')}?{query}"

    def process_callback(self, code: str | None, mock_user: str | None = None) -> dict:
        if self._settings.mock_auth_enabled and self._settings.is_test and mock_user:
            return {
                "user_id": mock_user,
                "tenant_id": self._settings.azure_tenant_id,
                "display_name": mock_user,
                "email": f"{mock_user}@example.test",
            }
        if mock_user and (not self._settings.mock_auth_enabled or not self._settings.is_test):
            raise AppError("Mock auth is disabled outside automated tests.", 401)
        if not code:
            raise AppError("Authentication failed: missing authorization code.", 401)
        token_url = self._oauth_endpoint("token")
        data = {
            "grant_type": "authorization_code",
            "client_id": self._settings.azure_client_id,
            "client_secret": self._settings.azure_client_secret,
            "code": code,
            "redirect_uri": self._settings.oidc_callback_url,
        }
        response = httpx.post(token_url, data=data, timeout=10.0)
        if response.status_code >= 400:
            raise AppError("Authentication failed: token exchange error.", 401)
        payload = response.json()
        id_token = payload.get("id_token", "")
        claims = _decode_jwt_payload(id_token)
        tid = claims.get("tid", "")
        if tid != self._settings.azure_tenant_id:
            raise AppError("Tenant mismatch. Access denied.", 401)
        return {
            "user_id": claims.get("oid", claims.get("sub", "")),
            "tenant_id": tid,
            "display_name": claims.get("name"),
            "email": claims.get("preferred_username"),
        }

    def create_session(self, user: dict) -> str:
        sid = str(uuid4())
        self._sessions[sid] = {
            "user": user,
            "authenticated_at": datetime.now(UTC).isoformat(),
            "expires_at": (datetime.now(UTC) + timedelta(hours=8)).isoformat(),
        }
        return sid

    def get_session_user(self, request: Request) -> dict:
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise AppError("Authentication required.", 401)
        session = self._sessions.get(session_id)
        if not session:
            raise AppError("Session expired. Please login again.", 401)
        if session["user"]["tenant_id"] != self._settings.azure_tenant_id:
            raise AppError("Tenant mismatch. Access denied.", 401)
        return session["user"]

    def get_optional_user(self, request: Request) -> dict | None:
        sid = request.cookies.get("session_id")
        if not sid:
            return None
        session = self._sessions.get(sid)
        return None if not session else session["user"]
