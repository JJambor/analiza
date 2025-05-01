import logging

from data_cache.redis_publisher import RedisPublisher

logger = logging.getLogger(__name__)

class CacheService:
    REDIS_LISTENER: RedisPublisher = None
    @staticmethod
    def publish(new_paths):
        if CacheService.REDIS_LISTENER is None:
            CacheService.REDIS_LISTENER = RedisPublisher.get_publisher()
        logger.debug("Publish new paths to Redis")
        CacheService.REDIS_LISTENER.publish(new_paths)

