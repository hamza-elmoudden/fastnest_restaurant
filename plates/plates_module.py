from fastnest.core.decorators import Module
from .plates_controller import PlatesController
from .plates_service import PlatesService


@Module(controllers=[PlatesController], providers=[PlatesService])
class PlatesModule:
    pass
