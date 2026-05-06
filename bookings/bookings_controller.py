from typing import Optional

from fastnest.core.decorators import Controller, Get, Post, Patch, Delete, UseGuard, UseInterceptor, UsePipe
from fastnest.core.params import Body, Param, Query
from fastnest.common.decorators import Roles
from fastnest.common.guards.roles_guard import RolesGuard
from fastnest.common.pipes import ValidationPipe

from shared.guards import JwtGuard
from shared.interceptors import LogInterceptor
from shared.decorators import CurrentUser
from .bookings_service import BookingsService
from .bookings_dto import CreateBookingDto


@UseGuard(JwtGuard)
@UseInterceptor(LogInterceptor)
@Controller("bookings")
class BookingsController:
    def __init__(self, svc: BookingsService):
        self.svc = svc

    @Get()
    async def find_all(
        self,
        status:   Optional[str] = Query(default=None),
        table_id: Optional[str] = Query(default=None),
        user=CurrentUser(),
    ):
        uid = None if user.get("role") in ("admin", "staff") else user["sub"]
        return await self.svc.find_all(user_id=uid, status=status, table_id=table_id)

    @Get("{booking_id}")
    async def find_one(self, booking_id: str = Param()):
        return await self.svc.find_one(booking_id)

    @Post()
    @UsePipe(ValidationPipe)
    async def create(self, body: CreateBookingDto = Body(), user=CurrentUser()):
        return await self.svc.create(body, user["sub"])

    @Patch("{booking_id}/activate")
    @Roles("admin", "staff")
    @UseGuard(RolesGuard)
    async def activate(self, booking_id: str = Param()):
        return await self.svc.activate(booking_id)

    @Patch("{booking_id}/complete")
    @Roles("admin", "staff")
    @UseGuard(RolesGuard)
    async def complete(self, booking_id: str = Param()):
        return await self.svc.complete(booking_id)

    @Delete("{booking_id}")
    async def cancel(self, booking_id: str = Param(), user=CurrentUser()):
        return await self.svc.cancel(booking_id, user)
