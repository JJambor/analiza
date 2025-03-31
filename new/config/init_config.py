from dotenv import load_dotenv
load_dotenv()
def load_config(app):
    app.config.update({
        'REDIS_URL': "redis://:HEhTvUYAKfd61DXCba17@kompas-cache:6379",
        'REDIS_DECODE_RESPONSES': True,
        'WTF_CSRF_ENABLED': False
    })