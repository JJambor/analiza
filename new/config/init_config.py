from dotenv import load_dotenv
import os

load_dotenv()
def load_config(app):
    app.config.update({
        'REDIS_URL': os.environ.get('REDIS_URL'),
        'REDIS_DECODE_RESPONSES':  os.environ.get('REDIS_DECODE_RESPONSES'),
        'WTF_CSRF_ENABLED': os.environ.get('WTF_CSRF_ENABLED')
    })
    app.secret_key = os.environ.get("SECRET")

