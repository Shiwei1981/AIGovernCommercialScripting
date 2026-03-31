from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from src.config.settings import Settings, get_settings


@dataclass
class AuthenticatedUser:
    user_id: str
    display_name: str | None
    tenant_id: str
    raw_claims: dict[str, Any]


def _decode_unverified(token: str) -> dict[str, Any]:
    try:
        return jwt.get_unverified_claims(token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token') from exc


def get_current_user(
    authorization: str = Header(default=''),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token')

    token = authorization.replace('Bearer ', '', 1).strip()
    claims = _decode_unverified(token)

    audience = claims.get('aud')
    issuer = claims.get('iss', '')
    tenant_id = claims.get('tid', '')
    user_id = claims.get('oid') or claims.get('sub')

    if audience not in {settings.entra_client_id, f"api://{settings.entra_client_id}"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token audience')
    if tenant_id != settings.entra_tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid tenant')
    if str(settings.entra_tenant_id) not in issuer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid issuer')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing user identity claim')

    return AuthenticatedUser(
        user_id=user_id,
        display_name=claims.get('name'),
        tenant_id=tenant_id,
        raw_claims=claims,
    )
