from flask import Flask

from views.auth import auth_bp, auth_form_bp
from views.home import home_bp
from main.app import create_dash

from auth_guard.guard import create_auth_manager, auth
from config.init_config import load_config
from redis_client.redis_client import create_redis_client
if __name__ == '__main__':

    app = Flask(__name__,template_folder='templates')
    app.before_request(auth)
    load_config(app)
    create_redis_client(app)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(auth_form_bp, url_prefix='/auth')
    app.register_blueprint(home_bp, url_prefix='/')
    app.secret_key = 'tajny-klucz-123'
    create_auth_manager(app)

    app = create_dash(app)
    app.run(host='0.0.0.0', port=8050, debug=True)