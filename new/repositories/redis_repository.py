import json
from redis_client.redis_client import redis
from entities.user import User
class RedisRepository:

    @staticmethod
    def cache_auth_user(user):
        redis.set(f"user-{user.id}", json.dumps(user.to_json()))

    @staticmethod
    def get_cached_user(id):
        user_data = redis.get(f"user-{id}")
        if user_data is not None:
            user = json.loads(user_data)
            user_entity = User(user['name'], user['email'])
            return user_entity
        return None