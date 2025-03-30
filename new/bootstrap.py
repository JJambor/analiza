from flask import Flask, jsonify, request
from views.auth import auth_bp, auth_form_bp
from main.app import create_dash
from sqlalchemy import create_engine


# # Integrujemy Dash z Flask
# dash_app = create_dash_app(flask_app)

if __name__ == '__main__':
    app = Flask(__name__,template_folder='templates')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(auth_form_bp, url_prefix='/auth')
    app.secret_key = 'tajny-klucz-123'
    app.config['WTF_CSRF_ENABLED'] = False
    # app = create_dash(app)

    app.run(host='0.0.0.0', port=8050, debug=True)