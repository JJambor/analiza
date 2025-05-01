from werkzeug.utils import secure_filename
import os
from enums.sheet_actions import SheetActions
from entities.sheet import Sheet
from exceptions.no_active_sheets import NoActiveSheets
from repositories.sheets_repository import SheetsRepository
from datetime import datetime
import logging

from validators.sheet_data_validator import SheetDataValidator

from shared.sheet_data_shared_service import SheetDataSharedService

from services.cache_service import CacheService


logger = logging.getLogger(__name__)

class SheetService:
    PATH = 'sheets'
    VALIDATOR = SheetDataValidator()
    @staticmethod
    def save_sheet(file):
        try:
            if file and file.filename:
                filename = secure_filename(file.filename)
                SheetService.VALIDATOR.validate_file(file)
                filepath = os.path.abspath(os.path.join(SheetService.PATH, filename))
                os.makedirs(SheetService.PATH, exist_ok=True)
                file.seek(0)
                file.save(filepath)
                sheet = Sheet(path=filepath, is_active=False)
                return SheetsRepository.add_sheet(sheet)
        except:
            raise

    @staticmethod
    def get_sheets():
        try:
            sheets = SheetsRepository.get_sheets()
            return sheets
        except Exception as e:
            raise

    @staticmethod
    def update_sheets(id_list, action):
        try:
            logger.info(f"Updating sheets")
            active_sheets = []
            sheets = SheetsRepository.get_sheets()
            logger.info(f"Sheets {[sheet.id for sheet in sheets]}")
            ids = [int(id) for id in id_list]
            for sheet in sheets:
                if sheet.id in ids:
                    logger.debug(sheet)
                    if action == SheetActions.Active.value:
                        sheet.is_active = True
                        active_sheets.append(sheet)
                    elif action == SheetActions.Disactive.value:
                        sheet.is_active = False
                    elif action == SheetActions.Delete.value:
                        sheet.is_active = False
                        sheet.deleted_at = datetime.now()
                if sheet.is_active:
                    active_sheets.append(sheet)
            if len(active_sheets) == 0:
                logger.error("Cannot find any active sheet")
                raise NoActiveSheets("Cannot find any active sheet")
            SheetsRepository.update_many_sheets(sheets)
            updated_sheets = [sheet.path for sheet in active_sheets]
            SheetService.update_plotly_sheets(updated_sheets)
        except Exception as e:
            logger.error(f"Error when trying update sheets: {e}")
            raise
    @staticmethod
    def get_sheets_for_plotly():
        try:
            sheets = SheetsRepository.get_active_sheets_paths()
            return sheets
        except Exception as e:
            raise

    @staticmethod
    def update_plotly_sheets(paths):
        try:
            SheetDataSharedService.update_sheets(paths)
            CacheService.publish(paths)
        except Exception as e:
            raise