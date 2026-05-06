import os
from fastnest.core.decorators import Injectable


@Injectable()
class ConfigService:
    def __init__(self):
        self._cfg = {
            "db_url":         os.getenv("DB_URL", "postgresql://postgres:123456789@localhost/restaurant_db"),
            "jwt_secret":     os.getenv("JWT_SECRET",     "restaurant-jwt-secret"),
            "refresh_secret": os.getenv("REFRESH_SECRET", "restaurant-refresh-secret"),
        }

    def get(self, k: str):
        return self._cfg[k]
