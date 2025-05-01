from flask import request, session, redirect, url_for
from flask_login import LoginManager,current_user, login_manager

from enums.user_role import UserRole
from services.users_service import UsersService
routes = ['/admin/users']
# routes = []
def create_super_admin_auth_manager(app):
       login_manager = LoginManager()
       login_manager.init_app(app)

       @login_manager.user_loader
       def load_user(id):
           user = UsersService.get_user(id)
           if user is None or user is False or not user.is_authenticated or not user.is_active:
               return None
           return user
def super_admin_auth():
    def check():

        for protected in routes:
            if request.path.startswith(protected):
                if not current_user.is_authenticated or current_user.role not in [UserRole.SUPER_ADMIN,
                                                                                  UserRole.COORDINATOR]:
                    return redirect('/dashboard')
    return check()