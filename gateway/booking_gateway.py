import os
import json
import time

from fastnest.core.websocket import (
    WebSocketGateway, SubscribeMessage,
    OnConnect, OnDisconnect, WebSocketClient,
)

from notifications.notifications_service import BookingNotificationService
from shared.jwt import _verify


@WebSocketGateway("/ws/bookings")
class BookingGateway:
    def __init__(self, notif: BookingNotificationService):
        self.notif = notif

    @OnConnect()
    async def on_connect(self, client: WebSocketClient):
        await client.send({"event": "connected", "data": {"client_id": client.id}})

    @OnDisconnect()
    async def on_disconnect(self, client: WebSocketClient):
        self.notif.leave_room(client)

    @SubscribeMessage("join")
    async def on_join(self, data: dict, client: WebSocketClient):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}

        token      = data.get("token", "")
        booking_id = data.get("booking_id", "")
        secret     = os.getenv("JWT_SECRET", "restaurant-jwt-secret")
        payload    = _verify(token, secret)

        if not payload:
            await client.send({"event": "error", "data": "Invalid token"})
            return

        self.notif.join_room(booking_id, client)
        await client.send({
            "event": "joined",
            "data":  {"booking_id": booking_id, "client_id": client.id},
        })

    @SubscribeMessage("join:admin")
    async def on_join_admin(self, data: dict, client: WebSocketClient):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}

        token   = data.get("token", "")
        secret  = os.getenv("JWT_SECRET", "restaurant-jwt-secret")
        payload = _verify(token, secret)

        if not payload or payload.get("role") not in ("admin", "staff"):
            await client.send({"event": "error", "data": "Unauthorized"})
            return

        self.notif.join_room("admin", client)
        await client.send({"event": "joined:admin", "data": {"client_id": client.id}})

    @SubscribeMessage("ping")
    async def on_ping(self, data, client: WebSocketClient):
        await client.send({"event": "pong", "data": {"ts": time.time()}})
