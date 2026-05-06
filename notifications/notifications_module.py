from fastnest.core.decorators import Module
from .notifications_service import BookingNotificationService


@Module(providers=[BookingNotificationService], exports=[BookingNotificationService])
class NotificationModule:
    pass
