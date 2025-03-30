from services.users_service import UsersService
from flask import Blueprint, render_template, request
import logging

logger = logging.getLogger(__name__)
class AuthController:

    @staticmethod
    def getLoginForm():
        return render_template("auth.html")
    @staticmethod
    def authUser():
        logger.info("Form data: %s", request.form)
        return render_template("auth.html")

        isLogin = UsersService.auth_user(request.form.get('email'), request.form.get('password'))
        if isLogin == True:
            return render_template("home.html")
        return render_template("auth.html")
