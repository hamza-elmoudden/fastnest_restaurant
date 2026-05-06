from typing import Optional

from fastnest.core.decorators import Controller, Get, Patch, UseGuard, UseInterceptor, UsePipe
from fastnest.core.params import Body, Param, Query
from fastnest.common.decorators import Roles
from fastnest.common.guards.roles_guard import RolesGuard
from fastnest.common.pipes import ValidationPipe

from shared.guards import JwtGuard
from shared.interceptors import LogInterceptor
from .tables_service import TablesService
from .tables_dto import UpdateTableDto


@UseGuard(JwtGuard)
@UseInterceptor(LogInterceptor)
@Controller("tables")
class TablesController:
    def __init__(self, svc: TablesService):
        self.svc = svc

    @Get()
    async def find_all(
        self,
        status:   Optional[str] = Query(default=None),
        location: Optional[str] = Query(default=None),
    ):
        return await self.svc.find_all(status, location)

    @Get("{table_id}")
    async def find_one(self, table_id: str = Param()):
        return await self.svc.find_one(table_id)

    @Patch("{table_id}")
    @Roles("admin", "staff")
    @UseGuard(RolesGuard)
    @UsePipe(ValidationPipe)
    async def update(self, table_id: str = Param(), body: UpdateTableDto = Body()):
        return await self.svc.update(table_id, body)
