from flask import current_app



class SheetDataSharedService:

    app = None

    @staticmethod
    def set_plotly(app):
        SheetDataSharedService.app = app
    @staticmethod
    def update_sheets(paths):
        if SheetDataSharedService.app is not None:
            if 'main_app' not in current_app.extensions:
                raise RuntimeError("MainApp not initialized!")
            SheetDataSharedService.app.reload_data(paths)

