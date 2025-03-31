from flask import Blueprint
from views.home_controller import HomeController
home_bp = Blueprint('home', __name__)
@home_bp.route('/', methods=['GET'])
def home_page():
    return HomeController.go_home()