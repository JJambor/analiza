from flask import render_template, request, redirect, flash
from services.sheet_service import SheetService
from entities.user import User
from services.users_service import UsersService
import logging
logger = logging.getLogger(__name__)
class AdminController:


    @staticmethod
    def list():
        logger.info("Listing datasheets")
        sheets = []
        try:
            sheets = SheetService.get_sheets()
            logger.info(f"Get sheets from database: {[sheet.id for sheet in sheets]}")
        except Exception as e:
            flash(f"{e}", "danger")
            logger.error("Error when trying get sheets")
        finally:
            return render_template("secure/datasheet_list.html", datasheets=sheets, error=False)

    @staticmethod
    def get_new_sheet_form():
        logger.info("Show add sheet form")
        return render_template('secure/add_sheet.html')

    @staticmethod
    def add_sheet():
        logger.info("Trying to add sheet")
        try:
            if not request.files or not request.files['file']:
                return redirect('/admin/datasheets/add-sheet')
            sheet = SheetService.save_sheet(request.files['file'])
            logger.info("Sheet was saved")
            return redirect('/admin/datasheets/list')
        except Exception as e:
            logger.error("Cannot add sheet, redirect to add-sheet")
            flash(f"{e}", "danger")
            return redirect('/admin/datasheets/add-sheet')


    @staticmethod
    def update_sheet(id, action):
        logger.info("Trying to update sheet")
        try:
            SheetService.update_sheets(id, action)
            logger.info(f"Successfully updated sheet {id}")
        except Exception as e :
            flash(f"{e}", "danger")
            logger.error(f"Cannot update sheet {id}")
        finally:
            logger.info("Redirect to sheets list")
            return redirect('/admin/datasheets/list')
    @staticmethod
    def get_users():
        users = []
        logger.info("Trying to get all of the users")
        try:
            users = UsersService.get_users()
            logger.info(f"Successfully get users: {[user.id for user in users]}")
        except Exception as e:
            users = []
            flash(f"{e}", "danger")
            logger.error("Cannot get users")
        finally:
            logger.info("Returning users list")
            return render_template('secure/users_list.html', users=users)

    @staticmethod
    def generate_link():
        logger.info("Generating link for a new user")
        link = None
        try:
            link = UsersService.generate_link_for_new_user()
            logger.info("Generated new register link")
            return render_template('secure/generate_link.html', link=link)

        except Exception as e:
            flash(f"{e}", "danger")
            logger.error("Cannot generate register link. Redirecting to users")
            return redirect("/admin/users/")

    @staticmethod
    def get_user_action(id):
        logger.info(f"Trying to get user: {id} from database")
        try:
            user = UsersService.get_user_from_db(id)
            logger.info("User get successfully")
            return render_template('secure/user_actions.html', user=user)
        except Exception as e:
            logger.error(f"Cannot get user {id} from database")
            return redirect("/admin/users")
    @staticmethod
    def change_user_action(id):
        logger.info(f"Trying to change user {id}")
        try:
            is_active_form = request.form.get('is_active')
            is_active = False
            if is_active_form == 'on':
                is_active = True
            user = User(
                email=request.form.get('email').strip(),
                name=request.form.get('name').strip(),
                role_value=request.form.get('role').strip(),
                is_active=is_active,
                id=id)
            user = UsersService.update_user(user)
            logger.info(f"Successfully updated user {id}")
        except Exception as e:
            flash(f"{e}", "danger")
            logger.error(f"Cannot get user {id} from database, error: {e}")
        finally:
            logger.info("Redirecting to users")
            return redirect("/admin/users")