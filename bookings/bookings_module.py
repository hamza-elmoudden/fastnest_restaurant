from fastnest.core.decorators import Module
from notifications.notifications_module import NotificationModule
from .bookings_controller import BookingsController
from .bookings_service import BookingsService


@Module(
    imports=[NotificationModule],
    controllers=[BookingsController],
    providers=[BookingsService],
)
class BookingsModule:
    pass
