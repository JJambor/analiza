from flask_redis import FlaskRedis

redis_sheets = FlaskRedis(config_prefix="REDIS_DATA")
def get_redis_sheets(app):
    redis_sheets.init_app(app)
    return redis_sheets