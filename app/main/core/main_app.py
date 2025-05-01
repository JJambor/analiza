import logging
from flask import Flask
from main.core.dash_app import DashApp
from main.core.dash_layout import DashLayout
from main.meta.dash_meta import DashMeta
from main.core.callbacks import Callbacks
from shared.sheet_shared_service import SheetSharedService
from validators.sheet_data_validator import SheetDataValidator
import traceback

logger = logging.getLogger(__name__)

class AppInitializationError(Exception):
    pass


class MainApp(metaclass=DashMeta):
    sheet_data_validator: SheetDataValidator
    app: DashApp = None
    layout: DashLayout = None
    flask_app: Flask = None
    callbacks: Callbacks = None
    initialization_successful: bool = False

    def __init__(self, flask_app: Flask):
        self.flask_app = flask_app
        self.flask_app.extensions['main_app'] = self
        self.sheet_data_validator = SheetDataValidator()
        self.__initialize()
        self.initialization_successful = True
        logger.info("MainApp initialized successfully.")

    def get_app(self):
         return self.app

    def get_layout_app(self):
        return self.layout

    def __initialize(self):

        logger.info("Initializing MainApp components.")
        try:
            paths = SheetSharedService.get_current_sheets()
            logger.info(f"Found {len(paths)} sheet paths.")
            self.__check_dataframe(paths)
            self.app = DashApp(self.flask_app, paths)
            self.layout = DashLayout(self.app)
            self.callbacks = Callbacks(self.app, self.layout)
            self.callbacks.register_callbacks()
            logger.info("Dash App, Layout, and Callbacks initialized.")
        except Exception as e:
            logger.critical(f"CRITICAL ERROR: Failed to initialize MainApp. Application may not function correctly. Exception: {e}\n{traceback.format_exc()}")

    def __check_dataframe(self, paths):
        logger.info(f"Checking dataframe paths: {paths}")
        if len(paths) == 0:
            error_msg = "Cannot find any sheet paths for validation."
            logger.error(error_msg)
            raise ValueError(error_msg)

        for path in paths:
            try:
                 self.sheet_data_validator.validate_existing_file(path)
                 logger.debug(f"Validation successful for path: {path}")
            except Exception as e:
                 logger.error(f"Validation failed for path: {path}. Exception: {e}\n{traceback.format_exc()}")
                 raise
        logger.info("All sheet paths validated.")


    def reload_data(self, paths):
        logger.info(f"Reloading data with paths: {paths}")
        try:
            self.app.reload(paths)
            self.sheet_data_validator = SheetDataValidator()
            self.layout = None
            self.layout = DashLayout(self.app)

            logger.info("Dash app reloaded successfully.")

        except Exception as e:
            logger.error(f"Error reloading data: {e}\n{traceback.format_exc()}")


