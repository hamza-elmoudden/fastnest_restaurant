from fastnest.core.decorators import Module

from config.config_module import ConfigModule
from database.database_module import DatabaseModule
from notifications.notifications_module import NotificationModule
from auth.auth_module import AuthModule
from tables.tables_module import TablesModule
from plates.plates_module import PlatesModule
from bookings.bookings_module import BookingsModule
from gateway.booking_gateway import BookingGateway


@Module(
    imports=[
        ConfigModule.for_root(),
        DatabaseModule,
        NotificationModule,
        AuthModule,
        TablesModule,
        PlatesModule,
        BookingsModule,
    ],
    gateways=[BookingGateway],
    providers=[],
)
class AppModule:
    pass
