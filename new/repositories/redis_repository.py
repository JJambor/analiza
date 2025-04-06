import json
from redis_client.redis_client import redis
from entities.user import User


class RedisRepository:

    @staticmethod
    def cache_auth_user(user):
        redis.setex(f"user-{user.id}", 360000, json.dumps(user.to_json()))

    @staticmethod
    def get_cached_user(id):
        user_data = redis.get(f"user-{id}")
        if user_data is not None:
            user = json.loads(user_data)
            user_entity = User(id=user['id'], name=user['name'], email=user['email'], role_value=user['role'], is_active=True)
            return user_entity
        return None
    @staticmethod
    def del_cached_user(id):
        redis.delete(f"user-{id}")