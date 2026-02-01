from flask import Blueprint, render_template, flash, redirect, url_for, request
from bson.objectid import ObjectId
from datetime import datetime
from extensions import mongo
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from flask import send_from_directory


user_bp = Blueprint('user', __name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route('/dashboard')
@login_required
def user_dashboard():
    user = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('auth.login'))

    # Format creation date if needed
    if isinstance(user.get('created_at'), str):
        try:
            user['created_at'] = datetime.strptime(user['created_at'], '%Y-%m-%d %H:%M:%S')
        except:
            user['created_at'] = None

    return render_template('dashboard_user.html', user=user)


# ------------------ EDIT USER PROFILE ------------------
@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('user.user_dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')

        update_data = {
            'full_name': full_name,
            'email': email,
            'phone_number': phone_number
        }

        # Handle profile image upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                update_data['profile_image'] = filename

        mongo.db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': update_data}
        )

        flash("Profile updated successfully.", "success")
        return redirect(url_for('user.user_dashboard'))

    return render_template('edit_profile_user.html', user=user)

@user_bp.route('/notifications')
@login_required
def view_notifications():
    notifications = list(mongo.db.notifications.find().sort('created_at', -1))
    return render_template('notifications_user.html', notifications=notifications)

@user_bp.route('/download/<filename>')
@login_required
def download_file(filename):
    from werkzeug.utils import secure_filename
    safe_filename = secure_filename(filename)
    return send_from_directory(UPLOAD_FOLDER, safe_filename, as_attachment=True)

