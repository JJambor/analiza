from flask import Flask, jsonify, request
from views.auth import auth_bp
from main.app import create_dash


# # Integrujemy Dash z Flask
# dash_app = create_dash_app(flask_app)

if __name__ == '__main__':
    app = Flask(__name__,template_folder='templates')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app = create_dash(app)
    app.run(host='0.0.0.0', port=8050, debug=True)