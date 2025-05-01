import threading

from flask import Flask

from auth_guard.signed_guard import signed_auth, create_signed_auth_manager
from auth_guard.super_admin_guard import super_admin_auth, create_super_admin_auth_manager
from data_cache.redis_listener import RedisListener
from data_cache.redis_publisher import RedisPublisher
from data_cache.redis_sheets import get_redis_sheets
from shared.sheet_data_shared_service import SheetDataSharedService
from views.auth import auth_bp, auth_form_bp, new_user_bp, new_user_post_bp, auth_logout_bp
from views.home import home_bp
from views.admin.admin import datasheet_bp, admin_root_bp, add_sheet_bp, get_add_sheet_bp, generate_link_bp, \
    get_users_bp, get_user_action_bp, change_user_data_bp, update_sheet_bp

from auth_guard.guard import create_auth_manager, auth
from  auth_guard.admin_guard import create_admin_auth_manager, admin_auth
from config.init_config import load_config
from redis_client.redis_client import create_redis_client
from main.core.main_app import MainApp

def get_app():
    app = Flask(__name__, template_folder='templates')


    load_config(app)
    redis_sheets = get_redis_sheets(app)
    create_redis_client(app)
    redis_listener = RedisListener(app, redis_sheets)
    redis_publisher = RedisPublisher(app, redis_sheets)
    redis_listener.start()
    main_app = MainApp(app)
    app.before_request(auth)
    app.before_request(admin_auth)
    app.before_request(super_admin_auth)
    app.before_request(signed_auth)
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
    app.register_blueprint(auth_logout_bp, url_prefix='/auth')
    app.register_blueprint(new_user_bp, url_prefix='/users')
    app.register_blueprint(get_user_action_bp, url_prefix='/admin')
    app.register_blueprint(new_user_post_bp, url_prefix='/users')
    app.register_blueprint(update_sheet_bp, url_prefix='/admin')
    create_auth_manager(app)
    create_admin_auth_manager(app)
    create_super_admin_auth_manager(app)
    create_signed_auth_manager(app)
    SheetDataSharedService.set_plotly(main_app)
    return app
if __name__ == '__main__':
    app = get_app()
    app.run(host='0.0.0.0', port=8050, debug=True)
