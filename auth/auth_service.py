import uuid
from datetime import datetime, timezone, timedelta

from fastnest.core.decorators import Injectable
from fastnest.common.exceptions import (
    ConflictException, UnauthorizedException, NotFoundException,
)
from fastnest.common.logger import Logger

from database.database_service import DatabaseService
from config.config_service import ConfigService
from shared.jwt import _hash, _make_tokens, _verify
from .auth_dto import RegisterDto, LoginDto, RefreshDto


@Injectable()
class AuthService:
    def __init__(self, db: DatabaseService, config: ConfigService):
        self.db     = db
        self.config = config
        self.logger = Logger("Auth")

    async def register(self, dto: RegisterDto) -> dict:
        if await self.db.fetchrow("SELECT id FROM users WHERE email=$1", dto.email):
            raise ConflictException(f"Email '{dto.email}' already registered")
        user = await self.db.fetchrow(
            "INSERT INTO users (name,email,password_hash,phone) "
            "VALUES ($1,$2,$3,$4) RETURNING id,name,email,role",
            dto.name, dto.email, _hash(dto.password), dto.phone,
        )
        self.logger.info(f"Registered {dto.email}")
        return user

    async def login(self, dto: LoginDto) -> dict:
        user = await self.db.fetchrow(
            "SELECT * FROM users WHERE email=$1 AND is_active=TRUE", dto.email
        )
        if not user or user["password_hash"] != _hash(dto.password):
            raise UnauthorizedException("Invalid credentials")
        tokens = _make_tokens(user, self.config.get("jwt_secret"),
                              self.config.get("refresh_secret"))
        exp = datetime.now(timezone.utc) + timedelta(days=7)
        await self.db.execute(
            "INSERT INTO refresh_tokens (user_id,token,expires_at) VALUES ($1,$2,$3) "
            "ON CONFLICT (token) DO NOTHING",
            uuid.UUID(user["id"]), tokens["refresh_token"], exp,
        )
        self.logger.info(f"Login: {dto.email}")
        return tokens

    async def refresh(self, dto: RefreshDto) -> dict:
        payload = _verify(dto.refresh_token, self.config.get("refresh_secret"))
        if not payload:
            raise UnauthorizedException("Invalid or expired refresh token")
        row = await self.db.fetchrow(
            "SELECT * FROM refresh_tokens WHERE token=$1 AND expires_at > NOW()",
            dto.refresh_token,
        )
        if not row:
            raise UnauthorizedException("Refresh token not found or expired")
        user = await self.db.fetchrow(
            "SELECT * FROM users WHERE id=$1", uuid.UUID(payload["sub"])
        )
        if not user:
            raise NotFoundException("User not found")
        await self.db.execute(
            "DELETE FROM refresh_tokens WHERE token=$1", dto.refresh_token
        )
        tokens = _make_tokens(user, self.config.get("jwt_secret"),
                              self.config.get("refresh_secret"))
        exp = datetime.now(timezone.utc) + timedelta(days=7)
        await self.db.execute(
            "INSERT INTO refresh_tokens (user_id,token,expires_at) VALUES ($1,$2,$3) "
            "ON CONFLICT (token) DO NOTHING",
            uuid.UUID(user["id"]), tokens["refresh_token"], exp,
        )
        return tokens

    async def logout(self, refresh_token: str) -> dict:
        await self.db.execute(
            "DELETE FROM refresh_tokens WHERE token=$1", refresh_token
        )
        return {"message": "Logged out successfully"}

    async def me(self, user_id: str) -> dict:
        user = await self.db.fetchrow(
            "SELECT id,name,email,role,phone,created_at FROM users WHERE id=$1",
            uuid.UUID(user_id),
        )
        if not user:
            raise NotFoundException("User not found")
        return user
