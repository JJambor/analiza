from flask import render_template, request, redirect
from services.sheet_service import SheetService
from entities.user import User
from services.users_service import UsersService
class AdminController:


    @staticmethod
    def list():
        current_sheets = []
        sheets = SheetService.get_sheets()
        return render_template("secure/datasheet_list.html", datasheets=sheets)

    @staticmethod
    def get_new_sheet_form():
        return render_template('secure/add_sheet.html')

    @staticmethod
    def add_sheet():
        if not request.files or not request.files['file']:
            return redirect('/admin/datasheets/add-sheet')
        sheet = SheetService.save_sheet(request.files['file'])
        if sheet == False:
            return redirect('/admin/datasheets/add-sheet')
        return redirect('/admin/datasheets/list')

    @staticmethod
    def get_users():
        users = UsersService.get_users()

        return render_template('secure/users_list.html', users=users)

    @staticmethod
    def generate_link():
        link = UsersService.generate_link_for_new_user()
        return render_template('secure/generate_link.html', link=link)

    @staticmethod
    def get_user_action(id):
        user = UsersService.get_user_from_db(id)
        return render_template('secure/user_actions.html', user=user)

    @staticmethod
    def change_user_action(id):
        is_active_form = request.form.get('is_active')
        is_active = False
        if is_active_form == 'on':
            is_active = True
        user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            role_value=request.form.get('role'),
            is_active=is_active,
            id=id)
        user = UsersService.update_user(user)
        return redirect("/admin/users")