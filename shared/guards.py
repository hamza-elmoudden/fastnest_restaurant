import os
from fastapi import Request
from fastnest.common.interfaces import CanActivate
from fastnest.common.exceptions import UnauthorizedException
from shared.jwt import _verify


class JwtGuard(CanActivate):
    def can_activate(self, request: Request) -> bool:
        secret = os.getenv("JWT_SECRET", "restaurant-jwt-secret")
        auth   = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise UnauthorizedException("Missing Authorization header")
        payload = _verify(auth.split(" ", 1)[-1].strip(), secret)
        if not payload:
            raise UnauthorizedException("Invalid or expired token")
        request.state.user = payload
        return True
