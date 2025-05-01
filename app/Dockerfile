FROM python:3.13.1

WORKDIR /app
RUN pip install gunicorn dash-bootstrap-components openpyxl pandas holidays plotly flask SQLAlchemy pymysql flask-login flask-redis python-dotenv bcrypt --use-deprecated=legacy-resolver
EXPOSE 8050:8050

#ENTRYPOINT ["python", "./bootstrap.py"]
ENTRYPOINT ["gunicorn", "-w", "4", "-b", "0.0.0.0:8050","--timeout","500", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-", "bootstrap:get_app()"]
