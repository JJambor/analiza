from flask import render_template, request, redirect, url_for
import logging
from services.users_service import UsersService

from entities.user import User

logger = logging.getLogger(__name__)
class AuthController:

    @staticmethod
    def getLoginForm():
        return render_template("open/auth.html")
    @staticmethod
    def authUser():
        logger.info("Form data: %s", request.form)
        user = User(email=request.form.get('email'), raw_password=request.form.get('password') )
        isLogin = UsersService.auth_user(user)
        if isLogin == True:
            return redirect("/dashboard")
        return redirect(url_for('auth_form.login_form'))
