from flask import Blueprint
from views.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__)
auth_form_bp = Blueprint('auth_form', __name__)
new_user_bp = Blueprint('new_user', __name__)
new_user_post_bp = Blueprint('new_user_post', __name__)
@auth_bp.route('/login',  methods=['POST'])
def login():
    return AuthController.auth_user()

@auth_form_bp.route("/login", methods=['GET'])
def login_form():
    return AuthController.get_login_form()

@new_user_bp.route('/new/<string:id>', methods=['GET'])
def new_user(id):
    return AuthController.add_new_user(id)

@new_user_post_bp.route('/new', methods=['POST'])
def add_user():
    return AuthController.register_user()