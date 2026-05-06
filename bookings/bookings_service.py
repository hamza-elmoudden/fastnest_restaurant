import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional, List

from fastnest.core.decorators import Injectable
from fastnest.common.exceptions import (
    NotFoundException, ForbiddenException,
    ConflictException, BadRequestException,
)
from fastnest.common.logger import Logger

from database.database_service import DatabaseService
from notifications.notifications_service import BookingNotificationService
from .bookings_dto import CreateBookingDto


@Injectable()
class BookingsService:
    def __init__(self, db: DatabaseService, notif: BookingNotificationService):
        self.db    = db
        self.notif = notif
        self.logger = Logger("Bookings")

    async def find_all(
        self,
        user_id:  str = None,
        status:   str = None,
        table_id: str = None,
    ) -> List[dict]:
        q = """
            SELECT b.*,
                   u.name AS user_name, u.email AS user_email,
                   t.number AS table_number, t.location AS table_location,
                   t.capacity AS table_capacity
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN restaurant_tables t ON b.table_id = t.id
            WHERE TRUE
        """
        args = []
        if user_id:
            args.append(uuid.UUID(user_id))
            q += f" AND b.user_id=${len(args)}"
        if status:
            args.append(status)
            q += f" AND b.status=${len(args)}::booking_status"
        if table_id:
            args.append(uuid.UUID(table_id))
            q += f" AND b.table_id=${len(args)}"
        q += " ORDER BY b.booked_at DESC"
        bookings = await self.db.fetch(q, *args)
        for b in bookings:
            b["plates"] = await self._get_plates(b["id"])
        return bookings

    async def find_one(self, booking_id: str) -> dict:
        b = await self.db.fetchrow(
            """
            SELECT b.*,
                   u.name AS user_name, u.email AS user_email,
                   t.number AS table_number, t.location AS table_location
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN restaurant_tables t ON b.table_id = t.id
            WHERE b.id=$1
            """,
            uuid.UUID(booking_id),
        )
        if not b:
            raise NotFoundException(f"Booking {booking_id} not found")
        b["plates"] = await self._get_plates(booking_id)
        return b

    async def _get_plates(self, booking_id: str) -> List[dict]:
        return await self.db.fetch(
            """
            SELECT bp.*, p.name AS plate_name, p.price, p.category
            FROM booking_plates bp
            JOIN plates p ON bp.plate_id = p.id
            WHERE bp.booking_id=$1
            """,
            uuid.UUID(booking_id),
        )

    async def create(self, dto: CreateBookingDto, user_id: str) -> dict:
        table = await self.db.fetchrow(
            "SELECT * FROM restaurant_tables WHERE id=$1", uuid.UUID(dto.table_id)
        )
        if not table:
            raise NotFoundException("Table not found")
        if table["status"] == "maintenance":
            raise BadRequestException("Table is under maintenance")

        booked_dt = datetime.fromisoformat(dto.booked_at)
        conflict  = await self.db.fetchrow(
            """
            SELECT id FROM bookings
            WHERE table_id=$1
              AND status IN ('pending','active')
              AND ABS(EXTRACT(EPOCH FROM (booked_at - $2::timestamptz))) < 7200
            """,
            uuid.UUID(dto.table_id), booked_dt,
        )
        if conflict:
            raise ConflictException("Table already booked for this time slot")

        booking = await self.db.fetchrow(
            "INSERT INTO bookings (user_id,table_id,booked_at,guests,notes) "
            "VALUES ($1,$2,$3,$4,$5) RETURNING *",
            uuid.UUID(user_id), uuid.UUID(dto.table_id),
            booked_dt, dto.guests, dto.notes,
        )

        for item in dto.plates:
            await self.db.execute(
                "INSERT INTO booking_plates (booking_id,plate_id,quantity,note) "
                "VALUES ($1,$2,$3,$4)",
                uuid.UUID(booking["id"]), uuid.UUID(item["plate_id"]),
                item.get("quantity", 1), item.get("note"),
            )

        self.logger.info(f"Booking created: {booking['id']}")
        created = await self.find_one(booking["id"])

        await self.notif.broadcast_to_room("admin", "booking:created", {
            "booking_id":   created["id"],
            "status":       "pending",
            "table_number": created.get("table_number"),
            "user_name":    created.get("user_name"),
            "booked_at":    created.get("booked_at"),
            "guests":       created.get("guests"),
        })
        asyncio.create_task(
            self.notif.schedule_activation(booking["id"], delay=180)
        )
        return created

    async def activate(self, booking_id: str) -> dict:
        b = await self.find_one(booking_id)
        if b["status"] != "pending":
            raise BadRequestException(f"Cannot activate booking with status '{b['status']}'")
        await self.db.fetchrow(
            "UPDATE bookings SET status='active', activated_at=NOW() WHERE id=$1 RETURNING *",
            uuid.UUID(booking_id),
        )
        await self.db.execute(
            "UPDATE restaurant_tables SET status='occupied' WHERE id=$1",
            uuid.UUID(b["table_id"]),
        )
        full    = await self.find_one(booking_id)
        payload = {
            "booking_id":   booking_id,
            "status":       "active",
            "table_number": full.get("table_number"),
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "message":      "Booking manually activated.",
        }
        await self.notif.broadcast_to_room(booking_id, "booking:activated", payload)
        await self.notif.broadcast_to_room("admin",     "booking:activated", payload)
        return full

    async def cancel(self, booking_id: str, requester: dict) -> dict:
        b        = await self.find_one(booking_id)
        is_owner = b["user_id"] == requester["sub"]
        is_staff = requester.get("role") in ("admin", "staff")
        if not (is_owner or is_staff):
            raise ForbiddenException("Not your booking")
        if b["status"] in ("completed", "cancelled"):
            raise BadRequestException(f"Cannot cancel '{b['status']}' booking")
        await self.db.execute(
            "UPDATE bookings SET status='cancelled' WHERE id=$1", uuid.UUID(booking_id)
        )
        await self.db.execute(
            "UPDATE restaurant_tables SET status='available' WHERE id=$1",
            uuid.UUID(b["table_id"]),
        )
        full    = await self.find_one(booking_id)
        payload = {
            "booking_id":   booking_id,
            "status":       "cancelled",
            "table_number": full.get("table_number"),
        }
        await self.notif.broadcast_to_room(booking_id, "booking:cancelled", payload)
        await self.notif.broadcast_to_room("admin",     "booking:cancelled", payload)
        return full

    async def complete(self, booking_id: str) -> dict:
        b = await self.find_one(booking_id)
        if b["status"] != "active":
            raise BadRequestException("Only active bookings can be completed")
        await self.db.execute(
            "UPDATE bookings SET status='completed' WHERE id=$1", uuid.UUID(booking_id)
        )
        await self.db.execute(
            "UPDATE restaurant_tables SET status='available' WHERE id=$1",
            uuid.UUID(b["table_id"]),
        )
        full    = await self.find_one(booking_id)
        payload = {
            "booking_id":   booking_id,
            "status":       "completed",
            "table_number": full.get("table_number"),
        }
        await self.notif.broadcast_to_room(booking_id, "booking:completed", payload)
        await self.notif.broadcast_to_room("admin",     "booking:completed", payload)
        return full
