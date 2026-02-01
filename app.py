
from flask import Flask, send_from_directory
from config import Config
from extensions import mongo, login_manager, mail
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
mongo.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.init_app(app)
mail.init_app(app)

# ------------------ BLUEPRINTS ------------------

# Import blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.user_routes import user_bp
from routes.main_routes import main_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(main_bp)

# ------------------ ROUTES ------------------

import os
from flask import render_template

@app.route("/admin/approvals")
def admin_approvals():
    mapbox_token = os.getenv("MAPBOX_TOKEN")  # set in your .env file
    return render_template("admin_approvals.html", MAPBOX_TOKEN=mapbox_token)


# Serve favicon.ico to avoid 404 errors in browser
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
    

from flask import send_file

@app.route('/download_video')
def download_video():
    video_path = 'static/violenceprof/20250810_153710_violence.mp4'
    return send_file(video_path, as_attachment=True)


# ------------------ MAIN ------------------

if __name__ == '__main__':
    app.run(debug=True)
# if __name__ == "__main__":
#     app.run(debug=False)
