from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO

# ✅ All extensions
mongo = PyMongo()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO()
