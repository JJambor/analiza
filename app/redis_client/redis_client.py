from flask_redis import FlaskRedis
redis = FlaskRedis()

def create_redis_client(app):
    redis.init_app(app)
    return redis
