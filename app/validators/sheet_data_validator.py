from werkzeug.utils import secure_filename
import os
import pandas as pd
class SheetDataValidator():

    ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'xltx', 'xls', 'xlt', 'xml', 'ods']
    REQUIRED_COLS = [
        'Netto',
        'Stacja',
        'Data'
    ]
    def validate_file(self, file):
        try:
            self.__valid_extension(file)
            self.__valid_data_scheme(file)
        except Exception as e:
            raise
    def validate_existing_file(self, path):
        try:
            self.__valid_data_scheme(path)
        except Exception as e:
            raise
    def __valid_extension(self, file):
        filename = secure_filename(file.filename)
        _, file_extension = os.path.splitext(filename)
        file_extension = file_extension.lstrip('.').lower()
        if file_extension in self.ALLOWED_EXTENSIONS:
            return True
        else:
            raise ValueError("Invalid extension")

    def __valid_data_scheme(self, file):
        df = self.__load_file(file)
        self.__validate_cols(df)

    def __load_file(self, file):
        try:
            return pd.read_excel(file, nrows=0)
        except Exception as e:
            raise

    def __validate_cols(self, df):
        try:
            for REQUIRED_COL in self.REQUIRED_COLS:
                if REQUIRED_COL not in df.columns:
                    raise ValueError(f"Column {REQUIRED_COL} does not exist")
        except Exception as e:
            raise
