from fastnest.core.decorators import Module
from .tables_controller import TablesController
from .tables_service import TablesService


@Module(controllers=[TablesController], providers=[TablesService])
class TablesModule:
    pass
