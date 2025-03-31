from flask import request, session, redirect, url_for
from flask_login import LoginManager,current_user, login_manager
from services.users_service import UsersService
# routes = ['/dashboard', '/admin']
routes = []

def create_auth_manager(app):
       login_manager = LoginManager()
       login_manager.init_app(app)

       @login_manager.user_loader
       def load_user(id):
           user = UsersService.get_user(id)
           if user is None or user is False or not user.is_authenticated:
               return None
           return user
def auth():
    def check():

        for protected in routes:
            if request.path.startswith(protected):
                if current_user is None or current_user is False or not current_user.is_authenticated:
                    return redirect(url_for('auth_form.login_form'))
    return check()