from flask import Flask

from views.auth import auth_bp, auth_form_bp, new_user_bp, new_user_post_bp
from views.home import home_bp
from views.admin.admin import datasheet_bp, admin_root_bp, add_sheet_bp, get_add_sheet_bp, generate_link_bp, \
    get_users_bp, get_user_action_bp, change_user_data_bp
from main.app import create_dash

from auth_guard.guard import create_auth_manager, auth
from  auth_guard.admin_guard import create_admin_auth_manager, admin_auth
from config.init_config import load_config
from redis_client.redis_client import create_redis_client


def get_app():
    app = Flask(__name__, template_folder='templates')
    app.before_request(auth)
    app.before_request(admin_auth)
    load_config(app)
    create_redis_client(app)
    app.register_blueprint(admin_root_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(auth_form_bp, url_prefix='/auth')
    app.register_blueprint(home_bp, url_prefix='/')
    app.register_blueprint(datasheet_bp, url_prefix='/admin')
    app.register_blueprint(add_sheet_bp,url_prefix='/admin')
    app.register_blueprint(get_add_sheet_bp,url_prefix='/admin')
    app.register_blueprint(get_users_bp, url_prefix='/admin')
    app.register_blueprint(generate_link_bp,url_prefix='/admin')
    app.register_blueprint(change_user_data_bp, url_prefix='/admin')

    app.register_blueprint(new_user_bp, url_prefix='/users')
    app.register_blueprint(get_user_action_bp, url_prefix='/admin')
    app.register_blueprint(new_user_post_bp, url_prefix='/users')
    app.secret_key = 'tajny-klucz-123'
    create_auth_manager(app)
    create_admin_auth_manager(app)

    # create_dash(app)

    return app
if __name__ == '__main__':
    app = get_app()
    app.run(host='0.0.0.0', port=8050, debug=True)
