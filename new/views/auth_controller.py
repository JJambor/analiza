from flask import render_template, request, redirect, url_for
import logging

from entities.magiclink import Magiclink
from services.users_service import UsersService

from entities.user import User

logger = logging.getLogger(__name__)
class AuthController:

    @staticmethod
    def get_login_form():
        return render_template("open/auth.html")
    @staticmethod
    def auth_user():
        logger.info("Form data: %s", request.form)
        user = User(email=request.form.get('email'), raw_password=request.form.get('password') )
        isLogin = UsersService.auth_user(user)
        if isLogin == True:
            return redirect("/dashboard")
        return redirect('/auth/login')

    @staticmethod
    def add_new_user(id):
        link_dto = Magiclink(link_value=id)
        found_link = UsersService.get_new_user_form(link_dto)
        if found_link is None:
            return render_template("open/not_found_link.html")
        else:
            return render_template("open/user_form.html")

    @staticmethod
    def register_user():
        user = User(email=request.form.get('email'), name=request.form.get('name'),  raw_password=request.form.get('password') )
        UsersService.register_user(user)
        return render_template("open/user_added.html")