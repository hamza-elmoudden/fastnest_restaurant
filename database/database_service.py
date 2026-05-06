import uuid
from datetime import datetime
from typing import Optional, List

import asyncpg
from fastnest.core.decorators import Injectable
from fastnest.common.lifecycle import OnModuleInit, OnModuleDestroy
from fastnest.common.logger import Logger

from config.config_service import ConfigService


@Injectable()
class DatabaseService(OnModuleInit, OnModuleDestroy):
    def __init__(self, config: ConfigService):
        self.config = config
        self.logger = Logger("DB")
        self._pool: Optional[asyncpg.Pool] = None

    async def on_module_init(self):
        self.logger.info("Connecting to PostgreSQL…")
        self._pool = await asyncpg.create_pool(
            self.config.get("db_url"), min_size=2, max_size=15
        )
        self.logger.info("PostgreSQL ready")

    async def on_module_destroy(self):
        if self._pool:
            await self._pool.close()

    def _serialize(self, row: dict) -> dict:
        result = {}
        for k, v in row.items():
            if isinstance(v, uuid.UUID):   result[k] = str(v)
            elif isinstance(v, datetime):  result[k] = v.isoformat()
            elif hasattr(v, "value"):      result[k] = v.value
            else:                          result[k] = v
        return result

    async def fetch(self, q: str, *args) -> List[dict]:
        async with self._pool.acquire() as c:
            rows = await c.fetch(q, *args)
            return [self._serialize(dict(r)) for r in rows]

    async def fetchrow(self, q: str, *args) -> Optional[dict]:
        async with self._pool.acquire() as c:
            row = await c.fetchrow(q, *args)
            return self._serialize(dict(row)) if row else None

    async def execute(self, q: str, *args) -> str:
        async with self._pool.acquire() as c:
            return await c.execute(q, *args)
