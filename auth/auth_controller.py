from fastnest.core.decorators import Controller, Get, Post, UseGuard, UseInterceptor, UsePipe
from fastnest.core.params import Body
from fastnest.common.pipes import ValidationPipe

from shared.guards import JwtGuard
from shared.interceptors import LogInterceptor
from shared.decorators import CurrentUser
from .auth_service import AuthService
from .auth_dto import RegisterDto, LoginDto, RefreshDto


@UseInterceptor(LogInterceptor)
@Controller("auth")
class AuthController:
    def __init__(self, svc: AuthService):
        self.svc = svc

    @Post("register")
    @UsePipe(ValidationPipe)
    async def register(self, body: RegisterDto = Body()):
        return await self.svc.register(body)

    @Post("login")
    @UsePipe(ValidationPipe)
    async def login(self, body: LoginDto = Body()):
        return await self.svc.login(body)

    @Post("refresh")
    @UsePipe(ValidationPipe)
    async def refresh(self, body: RefreshDto = Body()):
        return await self.svc.refresh(body)

    @Post("logout")
    async def logout(self, body: dict = Body()):
        return await self.svc.logout(body.get("refresh_token", ""))

    @Get("me")
    @UseGuard(JwtGuard)
    async def me(self, user=CurrentUser()):
        return await self.svc.me(user["sub"])
