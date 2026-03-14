"""Authentication middleware — dependency functions for each auth mode."""

from __future__ import annotations

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, HTTPBearer

from app.config import settings

basic_security = HTTPBasic()
bearer_security = HTTPBearer()


def _read_jwt_claims(token: str) -> dict:
    """Decode JWT payload without signature verification."""
    try:
        return jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_iss": False,
                "verify_exp": False,
            },
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )


async def verify_anonymous() -> None:
    """No-op auth for anonymous endpoints."""


async def verify_basic_auth(
    credentials: HTTPBasicCredentials = Depends(basic_security),
) -> None:
    """Validate Basic Auth credentials against configured values."""
    if (
        credentials.username != settings.basic_auth_username
        or credentials.password != settings.basic_auth_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


async def verify_api_key_header(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> None:
    """Validate API key from X-API-Key header."""
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


async def verify_entra_id_token(
    authorization: HTTPAuthorizationCredentials = Depends(bearer_security),
) -> None:
    """Validate Entra ID user token — reads JWT claims and checks UPN."""
    claims = _read_jwt_claims(authorization.credentials)

    upn = claims.get("upn") or claims.get("preferred_username") or ""
    if not upn:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain a UPN claim — is this a user token?",
        )

    authorized_upns = settings.get_authorized_upns()
    if authorized_upns and upn.lower() not in [u.lower() for u in authorized_upns]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"UPN '{upn}' is not authorized",
        )


async def verify_entra_id_appreg_token(
    authorization: HTTPAuthorizationCredentials = Depends(bearer_security),
) -> None:
    """Validate Entra ID app registration token (client_credentials flow)."""
    claims = _read_jwt_claims(authorization.credentials)

    app_id = claims.get("appid") or claims.get("azp") or ""
    if not app_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain an appid/azp claim — is this an app token?",
        )

    authorized_apps = settings.get_authorized_app_ids()
    if authorized_apps and app_id.lower() not in [a.lower() for a in authorized_apps]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"App ID '{app_id}' is not authorized",
        )
