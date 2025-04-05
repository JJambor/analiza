from flask import Blueprint
from views.admin.admin_controller import AdminController
datasheet_bp = Blueprint("datasheets_list", __name__)
admin_root_bp = Blueprint("admin_root", __name__)
get_add_sheet_bp = Blueprint('get_add_sheet', __name__)
add_sheet_bp = Blueprint('add_sheet', __name__)

get_user_action_bp = Blueprint('get_user_action', __name__)
get_users_bp = Blueprint('get_users', __name__)
generate_link_bp = Blueprint('generate_link', __name__)
change_user_data_bp = Blueprint('change_user_data', __name__)
@admin_root_bp.route('/')
def admin_root():
    return AdminController.list()

@datasheet_bp.route('/datasheets/list', methods=['GET'])
def get_datasheets():
    return AdminController.list()

@get_add_sheet_bp.route('/datasheets/add-sheet', methods=['GET'])
def get_add_sheet():
    return AdminController.get_new_sheet_form()
@add_sheet_bp.route('/datasheets/add-sheet', methods=['POST'])
def add_sheet():
    return AdminController.add_sheet()

@get_user_action_bp.route('/users/<int:id>', methods=['GET'])
def get_user_action(id):
    return AdminController.get_user_action(id)
@change_user_data_bp.route('/users/<int:id>', methods=['POST'])
def update_user(id):
    return AdminController.change_user_action(id)
@get_users_bp.route('/users', methods=['GET'])
def get_users():
    return AdminController.get_users()
@generate_link_bp.route('/users/link', methods=['GET'])
def generate_link():
    return AdminController.generate_link()