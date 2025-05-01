from repositories.sheets_repository import SheetsRepository

from shared.sheet_data_shared_service import SheetDataSharedService


class SheetSharedService:

    @staticmethod
    def get_current_sheets():
        return SheetsRepository.get_active_sheets_paths()
    @staticmethod
    def update_plotly():
        sheets = SheetsRepository.get_active_sheets_paths()
        return SheetDataSharedService.update_sheets(sheets)
