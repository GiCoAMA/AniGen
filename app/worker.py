from arq.connections import RedisSettings

from app.core.config import settings
from app.services.image_service import generate_image_task


class WorkerSettings:
    functions = [generate_image_task]
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port)

