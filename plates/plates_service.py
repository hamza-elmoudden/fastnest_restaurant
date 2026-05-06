import uuid
from typing import Optional, List

from fastnest.core.decorators import Injectable
from fastnest.common.exceptions import NotFoundException

from database.database_service import DatabaseService
from .plates_dto import CreatePlateDto


@Injectable()
class PlatesService:
    def __init__(self, db: DatabaseService):
        self.db = db

    async def find_all(self, category: str = None, available: bool = None) -> List[dict]:
        q    = "SELECT * FROM plates WHERE TRUE"
        args = []
        if category:
            args.append(category)
            q += f" AND category=${len(args)}"
        if available is not None:
            args.append(available)
            q += f" AND is_available=${len(args)}"
        q += " ORDER BY category, name"
        return await self.db.fetch(q, *args)

    async def find_one(self, plate_id: str) -> dict:
        p = await self.db.fetchrow(
            "SELECT * FROM plates WHERE id=$1", uuid.UUID(plate_id)
        )
        if not p:
            raise NotFoundException(f"Plate {plate_id} not found")
        return p

    async def create(self, dto: CreatePlateDto) -> dict:
        return await self.db.fetchrow(
            "INSERT INTO plates (name,description,price,category,image_url) "
            "VALUES ($1,$2,$3,$4,$5) RETURNING *",
            dto.name, dto.description, dto.price, dto.category, dto.image_url,
        )

    async def toggle_availability(self, plate_id: str) -> dict:
        await self.find_one(plate_id)
        return await self.db.fetchrow(
            "UPDATE plates SET is_available=NOT is_available WHERE id=$1 RETURNING *",
            uuid.UUID(plate_id),
        )
