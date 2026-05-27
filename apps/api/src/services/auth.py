from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuthIdentity:
    user_id: str


def resolve_identity(auth_mode: str, authorization_header: str | None) -> AuthIdentity:
    if not authorization_header or not authorization_header.lower().startswith("bearer "):
        raise ValueError("Missing bearer token")

    token = authorization_header.split(" ", 1)[1].strip()
    if not token:
        raise ValueError("Empty bearer token")

    if auth_mode == "dev":
        # Dev mode: token content becomes user id directly.
        return AuthIdentity(user_id=token)

    # Firebase token verification is intentionally strict in non-dev modes.
    # Integrate firebase-admin verification in the deployment environment.
    raise ValueError("auth_mode is not supported in this local build")
