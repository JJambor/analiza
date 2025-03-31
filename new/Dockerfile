FROM python:3.13.1

WORKDIR /app
RUN pip install dash-bootstrap-components openpyxl pandas holidays plotly flask SQLAlchemy pymysql flask-login flask-redis python-dotenv bcrypt --use-deprecated=legacy-resolver
EXPOSE 8050:8050

ENTRYPOINT ["python", "./bootstrap.py"]

