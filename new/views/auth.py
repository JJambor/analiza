from flask import Blueprint, render_template, request
from views.auth_controller import AuthController
auth_bp = Blueprint('auth', __name__)
auth_form_bp = Blueprint('auth_form', __name__)

@auth_bp.route('/login',  methods=['POST'])
def login():
    return AuthController.authUser()

@auth_form_bp.route("/login", methods=['GET'])
def loginForm():
    return AuthController.getLoginForm()