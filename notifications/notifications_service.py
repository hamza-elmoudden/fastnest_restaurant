import uuid
import asyncio
from datetime import datetime, timezone

from fastnest.core.decorators import Injectable
from fastnest.core.websocket import WebSocketClient
from fastnest.common.logger import Logger

from database.database_service import DatabaseService
from config.config_service import ConfigService


@Injectable()
class BookingNotificationService:
    def __init__(self, db: DatabaseService, config: ConfigService):
        self.db     = db
        self.config = config
        self.logger = Logger("WS-Notif")
        self._rooms: dict = {}

    def join_room(self, booking_id: str, client: WebSocketClient):
        self._rooms.setdefault(booking_id, [])
        if client not in self._rooms[booking_id]:
            self._rooms[booking_id].append(client)

    def leave_room(self, client: WebSocketClient):
        for room in self._rooms.values():
            if client in room:
                room.remove(client)

    async def broadcast_to_room(self, booking_id: str, event: str, data: dict):
        clients = self._rooms.get(booking_id, [])
        dead    = []
        for client in clients:
            try:
                await client.send({"event": event, "data": data})
            except Exception:
                dead.append(client)
        for d in dead:
            clients.remove(d)

    async def schedule_activation(self, booking_id: str, delay: int = 180):
        await asyncio.sleep(delay)
        try:
            booking = await self.db.fetchrow(
                "SELECT * FROM bookings WHERE id=$1 AND status='pending'",
                uuid.UUID(booking_id),
            )
            if not booking:
                return

            await self.db.execute(
                "UPDATE bookings SET status='active', activated_at=NOW() WHERE id=$1",
                uuid.UUID(booking_id),
            )
            await self.db.execute(
                "UPDATE restaurant_tables SET status='occupied' WHERE id=$1",
                booking["table_id"],
            )

            full = await self.db.fetchrow(
                """
                SELECT b.*, t.number AS table_number
                FROM bookings b
                JOIN restaurant_tables t ON b.table_id = t.id
                WHERE b.id=$1
                """,
                uuid.UUID(booking_id),
            )

            payload = {
                "booking_id":   booking_id,
                "status":       "active",
                "table_number": full["table_number"] if full else None,
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "message":      "Your table is now active! Welcome to the restaurant.",
            }
            await self.broadcast_to_room(booking_id, "booking:activated", payload)
            await self.broadcast_to_room("admin",     "booking:activated", payload)
            self.logger.info(f"Auto-activated booking {booking_id}")
        except Exception as e:
            self.logger.error(f"Auto-activation failed for {booking_id}: {e}")
