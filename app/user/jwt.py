from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.settings.jwt import jwt_settings


class InvalidJWTTokenException(Exception):
    """Exception raised when incoming JWT token is invalid for any reason (expired, malformed, etc.)."""

    pass


class JWTService:
    @staticmethod
    def create_access_token(user_id: str, token_version: int) -> str:
        payload = {
            "iss": user_id,
            "ver": token_version,
            "exp": datetime.now(timezone.utc)
            + timedelta(hours=1),  # Token expires in 1 hour
        }
        return JWTService.encode(payload)

    @staticmethod
    def encode(payload: dict[str, Any]) -> str:
        return jwt.encode(
            payload=payload,
            key=jwt_settings.secret_key,
            algorithm=jwt_settings.algorithm,
        )

    @staticmethod
    def decode(token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                jwt=token,
                key=jwt_settings.secret_key,
                algorithms=[jwt_settings.algorithm],
            )
            if "iss" not in payload or "ver" not in payload or "exp" not in payload:
                raise InvalidJWTTokenException()
            return payload
        except Exception as e:
            raise InvalidJWTTokenException() from e
