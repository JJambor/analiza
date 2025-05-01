from data_cache.redis_publisher_meta import RedisPublisherMeta
import logging

from data_cache.redis_sheets_data import RedisSheetsData

logger = logging.getLogger(__name__)
class RedisPublisher(metaclass=RedisPublisherMeta):
    redis_publisher = None
    app = None
    running = False
    callback = None
    def __init__(self, app, redis):
        self.app = app
        self.redis_publisher = redis

    @staticmethod
    def get_publisher():
        return RedisPublisher._instance


    def publish(self,new_paths):
        logger.info("Publishing message")
        with self.redis_publisher.pipeline() as pipe:
            pipe.delete(RedisSheetsData.PATHS_KEY)
            pipe.rpush(RedisSheetsData.PATHS_KEY, *new_paths)
            pipe.incr(RedisSheetsData.DATA_VERSION_KEY)
            pipe.execute()
        self.redis_publisher.publish(RedisSheetsData.REDIS_TOPIC_NAME, RedisSheetsData.REDIS_TOPIC_VALUE)