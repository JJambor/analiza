from werkzeug.utils import secure_filename
import os

from entities.sheet import Sheet
from repositories.sheets_repository import SheetsRepository


class SheetService:
    ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'xltx', 'xls', 'xlt', 'xml', 'ods']
    PATH = 'sheets'

    @staticmethod
    def save_sheet(file):
        if file and file.filename:
            filename = secure_filename(file.filename)
            _, file_extension = os.path.splitext(filename)
            file_extension = file_extension.lstrip('.').lower()

            if file_extension in SheetService.ALLOWED_EXTENSIONS:
                filepath = os.path.abspath(os.path.join(SheetService.PATH, filename))
                os.makedirs(SheetService.PATH, exist_ok=True)
                file.save(filepath)
                sheet = Sheet(path=filepath)
                return SheetsRepository.add_sheet(sheet)
            else:
                return False
        return False

    @staticmethod
    def get_sheets():
        sheets = SheetsRepository.get_sheets()
        return sheets