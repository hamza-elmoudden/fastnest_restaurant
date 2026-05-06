import uuid
from typing import Optional, List

from fastnest.core.decorators import Injectable
from fastnest.common.exceptions import NotFoundException, BadRequestException

from database.database_service import DatabaseService
from .tables_dto import UpdateTableDto


@Injectable()
class TablesService:
    def __init__(self, db: DatabaseService):
        self.db = db

    async def find_all(self, status: str = None, location: str = None) -> List[dict]:
        q    = "SELECT * FROM restaurant_tables WHERE TRUE"
        args = []
        if status:
            args.append(status)
            q += f" AND status=${len(args)}::table_status"
        if location:
            args.append(location)
            q += f" AND location=${len(args)}"
        q += " ORDER BY number"
        return await self.db.fetch(q, *args)

    async def find_one(self, table_id: str) -> dict:
        t = await self.db.fetchrow(
            "SELECT * FROM restaurant_tables WHERE id=$1", uuid.UUID(table_id)
        )
        if not t:
            raise NotFoundException(f"Table {table_id} not found")
        return t

    async def update(self, table_id: str, dto: UpdateTableDto) -> dict:
        await self.find_one(table_id)
        sets, vals = [], []
        if dto.status is not None:
            vals.append(dto.status)
            sets.append(f"status=${len(vals)}::table_status")
        if dto.capacity is not None:
            vals.append(dto.capacity)
            sets.append(f"capacity=${len(vals)}")
        if dto.location is not None:
            vals.append(dto.location)
            sets.append(f"location=${len(vals)}")
        if not sets:
            raise BadRequestException("Nothing to update")
        vals.append(uuid.UUID(table_id))
        return await self.db.fetchrow(
            f"UPDATE restaurant_tables SET {','.join(sets)} "
            f"WHERE id=${len(vals)} RETURNING *",
            *vals,
        )
