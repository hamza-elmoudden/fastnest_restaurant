from typing import Optional

from fastnest.core.decorators import Controller, Get, Post, Patch, UseGuard, UseInterceptor, UsePipe
from fastnest.core.params import Body, Param, Query
from fastnest.common.decorators import Roles
from fastnest.common.guards.roles_guard import RolesGuard
from fastnest.common.pipes import ValidationPipe

from shared.guards import JwtGuard
from shared.interceptors import LogInterceptor
from .plates_service import PlatesService
from .plates_dto import CreatePlateDto


@UseInterceptor(LogInterceptor)
@Controller("plates")
class PlatesController:
    def __init__(self, svc: PlatesService):
        self.svc = svc

    @Get()
    async def find_all(
        self,
        category:  Optional[str]  = Query(default=None),
        available: Optional[bool] = Query(default=None),
    ):
        return await self.svc.find_all(category, available)

    @Get("{plate_id}")
    async def find_one(self, plate_id: str = Param()):
        return await self.svc.find_one(plate_id)

    @Post()
    @UseGuard(JwtGuard)
    @Roles("admin")
    @UseGuard(RolesGuard)
    @UsePipe(ValidationPipe)
    async def create(self, body: CreatePlateDto = Body()):
        return await self.svc.create(body)

    @Patch("{plate_id}/toggle")
    @UseGuard(JwtGuard)
    @Roles("admin", "staff")
    @UseGuard(RolesGuard)
    async def toggle(self, plate_id: str = Param()):
        return await self.svc.toggle_availability(plate_id)
