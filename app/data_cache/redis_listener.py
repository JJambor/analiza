import threading


from data_cache.redis_listener_meta import RedisListenerMeta
import logging

from data_cache.redis_sheets_data import RedisSheetsData
from shared.sheet_shared_service import SheetSharedService

logger = logging.getLogger(__name__)
class RedisListener(metaclass=RedisListenerMeta):

    redis_listener = None
    app = None
    running = False
    callback = None
    def __init__(self, app, redis):
        self.app = app
        self.redis_listener = redis

    @staticmethod
    def get_listener():
        return RedisListener._instance
    def _listen(self):
        try:
            with self.app.app_context():
                pubsub = self.redis_listener.pubsub()
                pubsub.subscribe(RedisSheetsData.REDIS_TOPIC_NAME)

                for message in pubsub.listen():
                    if not self.running:
                        break

                    if message['type'] == 'message':
                        decoded_data = message['data'].decode('utf-8')
                        if decoded_data == RedisSheetsData.REDIS_TOPIC_VALUE:
                            logger.debug("Received a new update event")
                            SheetSharedService.update_plotly()
        except Exception as e:
            print(f"Redis listener error: {str(e)}")
        finally:
            pubsub.close()

    def start(self):
        logger.info("Start redis listener")
        self.running = True
        threading.Thread(target=self._listen, daemon=True).start()

