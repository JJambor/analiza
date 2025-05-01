
class RedisSheetsData:

    DATA_VERSION_KEY = "data_version"
    PATHS_KEY = "excel_paths"
    CACHE_KEY_PREFIX = "excel_cache_"
    REDIS_TOPIC_NAME = "data_updates"
    REDIS_TOPIC_VALUE = "full_refresh"