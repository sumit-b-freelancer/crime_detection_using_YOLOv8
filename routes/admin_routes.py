from flask import Blueprint, render_template, redirect, url_for, abort, flash, request
from bson.objectid import ObjectId
from flask_login import login_required, current_user
from extensions import mongo, mail
from flask_mail import Message
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from flask import send_from_directory

admin_bp = Blueprint('admin', __name__)

# ------------------ UPLOAD SETTINGS ------------------
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ ADMIN DASHBOARD ------------------
@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)

    users_collection = mongo.db.users
    pending_users = list(users_collection.find({'status': 'pending'}))
    approved_users = list(users_collection.find({'status': 'approved'}))

    # For demo, hardcoded news stats
    total_news = 1200
    real_news = 850
    fake_news = 350

    return render_template(
        'dashboard_admin.html',
        pending_users=pending_users,
        approved_users=approved_users,
        total_news=total_news,
        real_news=real_news,
        fake_news=fake_news
    )

# ------------------ APPROVE USER ------------------
@admin_bp.route('/admin/approve/<user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        abort(403)

    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user:
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'approved'}})

        user_name = user.get('full_name', 'User')

        msg = Message(
            'Account Approved',
            sender=os.getenv('MAIL_USERNAME'),
            recipients=[user['email']]
        )
        msg.body = f"""
Dear {user_name},

Congratulations! Your account has been approved.
You can now log in and start using all the features.

Welcome aboard!

Regards,
Admin Team
"""
        mail.send(msg)

    flash('User approved successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

# ------------------ REJECT USER ------------------
@admin_bp.route('/admin/reject/<user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    if current_user.role != 'admin':
        abort(403)

    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user:
        user_name = user.get('full_name', 'User')

        msg = Message(
            'Account Registration Update',
            sender=os.getenv('MAIL_USERNAME'),
            recipients=[user['email']]
        )
        msg.body = f"""
Dear {user_name},

Thank you for registering with us.
After careful review, we regret to inform you that your account request has been declined at this time.

If you wish to reapply in the future or have questions, feel free to contact us.

Regards,
Admin Team
"""
        mail.send(msg)

        mongo.db.users.delete_one({'_id': ObjectId(user_id)})

    flash('User rejected and deleted successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))


# ------------------ UNAPPROVE USER ------------------
@admin_bp.route('/admin/unapprove/<user_id>', methods=['POST'])
@login_required
def unapprove_user(user_id):
    if current_user.role != 'admin':
        abort(403)

    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.admin_dashboard'))

    # Get reason from form
    reason = request.form.get('reason', 'No reason provided.')

    # Update user status to pending (unapproved)
    mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'pending'}})

    user_name = user.get('full_name', 'User')

    # Send email with reason
    msg = Message(
        'Account Status Update',
        sender=os.getenv('MAIL_USERNAME'),
        recipients=[user['email']]
    )
    msg.body = f"""
Dear {user_name},

This is to inform you that your account status has been changed to unapproved (pending review).

Reason: {reason}

If you have any questions, please contact the admin team.

Regards,
Admin Team
"""
    mail.send(msg)

    flash('User has been unapproved successfully.', 'success')
    return redirect(url_for('admin.user_profile', user_id=user_id))

# ------------------ VIEW USER PROFILE ------------------
@admin_bp.route('/admin/user/<user_id>')
@login_required
def user_profile(user_id):
    if current_user.role != 'admin':
        abort(403)

    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return "User not found", 404

    return render_template('user_profile.html', user=user)

# ------------------ EDIT ADMIN PROFILE ------------------
@admin_bp.route('/admin/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')

        update_data = {
            'full_name': full_name,
            'email': email,
            'phone_number': phone_number
        }

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

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    user = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    return render_template('edit_profile_admin.html', user=user)


# View notification form
@admin_bp.route('/admin/notifications', methods=['GET', 'POST'])
@login_required
def admin_notifications():
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        file = request.files.get('file')
        file_name = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            file_name = filename

        # Insert the notification
        mongo.db.notifications.insert_one({
            'title': title,
            'message': message,
            'file': file_name,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # Fetch all user emails
        users = mongo.db.users.find({}, {"email": 1})
        recipient_emails = [user['email'] for user in users if 'email' in user]

        # Send emails
        subject = f"📢 New Notification: {title}"
        body = f"Hello,\n\nA new notification has been posted by the Admin:\n\nTitle: {title}\nMessage: {message}"

        msg = Message(subject, recipients=recipient_emails)
        msg.body = body
        mail.send(msg)

        flash("Notification posted and email sent to all users.", "success")
        return redirect(url_for('admin.admin_notifications'))

    notifications = list(mongo.db.notifications.find().sort('created_at', -1))
    return render_template('notifications_admin.html', notifications=notifications)

@admin_bp.route('/download/<filename>')
@login_required
def download_file_admin(filename):
    from werkzeug.utils import secure_filename
    safe_filename = secure_filename(filename)
    return send_from_directory(UPLOAD_FOLDER, safe_filename, as_attachment=True)
from flask import Blueprint, request, redirect, url_for, render_template, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from bson.objectid import ObjectId

# Create blueprint for admin routes
# admin_bp = Blueprint('admin', __name__)

# Folder for storing criminal photos
CRIMINALS_FOLDER = os.path.join('static', 'criminals')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------
# Add & List Complaints
# -------------------
# @admin_bp.route('/admin/complaints', methods=['GET', 'POST'])
# def manage_complaints():
    from app import mongo  # Import inside function to avoid circular import

    if request.method == 'POST':
        name = request.form.get('name')
        crime_type = request.form.get('crime_type')
        details = request.form.get('details')
        file = request.files.get('photo')

        # Validate fields
        if not name or not crime_type or not details or not file:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.manage_complaints'))

        # Save file if valid
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(CRIMINALS_FOLDER, filename)
            os.makedirs(CRIMINALS_FOLDER, exist_ok=True)
            file.save(filepath)

            # Insert into MongoDB
            mongo.db.complaints.insert_one({
                "name": name,
                "crime_type": crime_type,
                "details": details,
                "photo": filepath,
                "status": "active",
                "created_at": datetime.utcnow()
            })

            flash('Complaint added successfully.', 'success')
        else:
            flash('Invalid file type.', 'danger')

        return redirect(url_for('admin.manage_complaints'))

    # GET request → List all complaints
    complaints = list(mongo.db.complaints.find().sort("created_at", -1))
    return render_template('admin_complaints.html', complaints=complaints)

# -------------------
# manage Complaint 
# -------------------
@admin_bp.route('/admin/complaints', methods=['GET', 'POST'])
def manage_complaints():
    from app import mongo
    from werkzeug.utils import secure_filename
    import os
    from datetime import datetime
    from flask import request, redirect, url_for, flash, render_template

    # Save in "static/criminals" folder
    CRIMINALS_FOLDER = os.path.join('static', 'criminals')

    def allowed_file(filename):
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if request.method == 'POST':
        name = request.form.get('name')
        crime_type = request.form.get('crime_type')
        details = request.form.get('details')
        file = request.files.get('photo')

        if not name or not crime_type or not details or not file:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.manage_complaints'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(CRIMINALS_FOLDER, exist_ok=True)
            filepath = os.path.join(CRIMINALS_FOLDER, filename)
            file.save(filepath)

            # Store Windows-style path
            stored_path = filepath.replace("/", "\\")  

            mongo.db.complaints.insert_one({
                "name": name,
                "crime_type": crime_type,
                "details": details,
                "photo": stored_path,
                "status": "active",
                "created_at": datetime.utcnow(),
                "detections": []
            })

            flash('Complaint added successfully.', 'success')
        else:
            flash('Invalid file type.', 'danger')

        return redirect(url_for('admin.manage_complaints'))

    complaints = list(mongo.db.complaints.find().sort("created_at", -1))
    return render_template('admin_complaints.html', complaints=complaints)



# -------------------
# Change Complaint Status
# -------------------
@admin_bp.route('/admin/complaints/status/<complaint_id>/<new_status>')
def change_complaint_status(complaint_id, new_status):
    from app import mongo
    if new_status not in ['active', 'inactive']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.manage_complaints'))

    mongo.db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {"$set": {"status": new_status}}
    )
    flash('Complaint status updated.', 'success')
    return redirect(url_for('admin.manage_complaints'))







# -------------------
# View Detections
# -------------------

# @admin_bp.route("/admin/detections")
# def show_detections():
#     from app import mongo
#
#     # Criminal detections from complaints
#     complaints = list(mongo.db.complaints.find())
#     all_detections = []
#     for complaint in complaints:
#         detections = complaint.get("detections", [])
#         for det in detections:
#             det = det.copy()
#             det["crime_type"] = complaint.get("crime_type", "N/A")
#             det["details"] = complaint.get("details", "N/A")
#             all_detections.append(det)
#     all_detections.sort(key=lambda d: (d.get("date", ""), d.get("time", "")), reverse=True)
#
#     # Weapon detections from separate table
#     weapon_detections = list(mongo.db.weapon_detection.find())
#     weapon_detections.sort(key=lambda d: (d.get("date", ""), d.get("time", "")), reverse=True)
#
#     # Violence detections from violence_detections collection
#     violence_detections = list(mongo.db.violence_detections.find())
#     violence_detections.sort(key=lambda d: (d.get("date", ""), d.get("time", "")), reverse=True)
#
#     return render_template(
#         "admin_detections.html",
#         detections=all_detections,
#         weapon_detections=weapon_detections,
#         violence_detections=violence_detections
#     )
#
@admin_bp.route("/admin/detections")
def show_detections():
    from app import mongo

    # ---- CRIMINAL DETECTIONS (Grouped by Complaint ID) ----
    complaints = list(mongo.db.complaints.find())
    criminal_grouped = {}
    for complaint in complaints:
        cid = str(complaint.get("_id"))
        detections = complaint.get("detections", [])
        for det in detections:
            det = det.copy()
            det["crime_type"] = complaint.get("crime_type", "N/A")
            det["details"] = complaint.get("details", "N/A")
            criminal_grouped.setdefault(cid, []).append(det)

    # Sort each complaint’s detections by date/time
    for cid in criminal_grouped:
        criminal_grouped[cid].sort(
            key=lambda d: (d.get("date", ""), d.get("time", "")),
            reverse=True
        )

    # ---- WEAPON DETECTIONS (Flat list) ----
    weapon_detections = list(mongo.db.weapon_detection.find())
    weapon_detections.sort(
        key=lambda d: (d.get("date", ""), d.get("time", "")),
        reverse=True
    )

    # ---- VIOLENCE DETECTIONS (Flat list) ----
    violence_detections = list(mongo.db.violence_detections.find())
    violence_detections.sort(
        key=lambda d: (d.get("date", ""), d.get("time", "")),
        reverse=True
    )

    mapbox_token = os.getenv("MAPBOX_TOKEN")
    return render_template(
        "admin_detections.html",
        criminal_grouped=criminal_grouped,
        weapon_detections=weapon_detections,
        violence_detections=violence_detections,
        MAPBOX_TOKEN=mapbox_token
    )


#
# from flask import Blueprint, render_template, Response, stream_with_context, jsonify
# import subprocess
# import threading
# import queue
#
# # admin_bp = Blueprint('admin', __name__)
#
# # Log queues
# criminal_log_queue = queue.Queue()
# weapon_log_queue = queue.Queue()
# violence_log_queue = queue.Queue()
#
# # Global subprocess handles
# criminal_process = None
# weapon_process = None
# violence_process = None
#
# def enqueue_output(out, log_queue):
#     for line in iter(out.readline, b''):
#         text = line.decode('utf-8').strip()
#         # Filter or pass all logs; add your tags if needed
#         if text:
#             log_queue.put(text)
#     out.close()
#
# def start_detection_process(script_name, process_var_name, log_queue):
#     global_vars = globals()
#     proc = global_vars.get(process_var_name)
#     if proc is not None and proc.poll() is None:
#         return False  # already running
#     proc = subprocess.Popen(
#         ['python', '-u', script_name],
#         stdout=subprocess.PIPE,
#         stderr=subprocess.STDOUT
#     )
#     global_vars[process_var_name] = proc
#     threading.Thread(target=enqueue_output, args=(proc.stdout, log_queue), daemon=True).start()
#     return True
#
# def stop_detection_process(process_var_name):
#     global_vars = globals()
#     proc = global_vars.get(process_var_name)
#     if proc and proc.poll() is None:
#         proc.terminate()
#         global_vars[process_var_name] = None
#         return True
#     return False
#
# def generate_logs(log_queue):
#     def generate():
#         while True:
#             try:
#                 line = log_queue.get(timeout=0.5)
#                 yield f"data: {line}\n\n"
#             except queue.Empty:
#                 yield ": keep-alive\n\n"
#     return Response(stream_with_context(generate()), mimetype='text/event-stream')
#
# @admin_bp.route('/admin/detection_control')
# def detection_control():
#     return render_template('admin_detection_control.html')
#
# # Criminal detection routes
# @admin_bp.route('/admin/start_criminal_detection')
# def start_criminal_detection():
#     started = start_detection_process('detector.py', 'criminal_process', criminal_log_queue)
#     if started:
#         return jsonify(ok=True, message="Criminal detection started.")
#     return jsonify(ok=False, message="Criminal detection already running.")
#
# @admin_bp.route('/admin/stop_criminal_detection')
# def stop_criminal_detection():
#     stopped = stop_detection_process('criminal_process')
#     if stopped:
#         return jsonify(ok=True, message="Criminal detection stopped.")
#     return jsonify(ok=False, message="Criminal detection was not running.")
#
# @admin_bp.route('/admin/criminal_detection_logs')
# def criminal_detection_logs():
#     return generate_logs(criminal_log_queue)
#
# # Weapon detection routes
# @admin_bp.route('/admin/start_weapon_detection')
# def start_weapon_detection():
#     started = start_detection_process('gun_webcam_test.py', 'weapon_process', weapon_log_queue)
#     if started:
#         return jsonify(ok=True, message="Weapon detection started.")
#     return jsonify(ok=False, message="Weapon detection already running.")
#
# @admin_bp.route('/admin/stop_weapon_detection')
# def stop_weapon_detection():
#     stopped = stop_detection_process('weapon_process')
#     if stopped:
#         return jsonify(ok=True, message="Weapon detection stopped.")
#     return jsonify(ok=False, message="Weapon detection was not running.")
#
# @admin_bp.route('/admin/weapon_detection_logs')
# def weapon_detection_logs():
#     return generate_logs(weapon_log_queue)
#
# # Violence detection routes
# @admin_bp.route('/admin/start_violence_detection')
# def start_violence_detection():
#     started = start_detection_process('violence_detect.py', 'violence_process', violence_log_queue)
#     if started:
#         return jsonify(ok=True, message="Violence detection started.")
#     return jsonify(ok=False, message="Violence detection already running.")
#
# @admin_bp.route('/admin/stop_violence_detection')
# def stop_violence_detection():
#     stopped = stop_detection_process('violence_process')
#     if stopped:
#         return jsonify(ok=True, message="Violence detection stopped.")
#     return jsonify(ok=False, message="Violence detection was not running.")
#
# @admin_bp.route('/admin/violence_detection_logs')
# def violence_detection_logs():
#     return generate_logs(violence_log_queue)
import os
import sys
import subprocess
import threading
import queue
from flask import Blueprint, render_template, Response, stream_with_context, jsonify

# ---------------------- BLUEPRINT ----------------------
#admin_bp = Blueprint('admin', __name__)

# ---------------------- LOG QUEUES ----------------------
criminal_log_queue = queue.Queue()
weapon_log_queue = queue.Queue()
violence_log_queue = queue.Queue()

# ---------------------- PROCESS HANDLES ----------------------
criminal_process = None
weapon_process = None
violence_process = None


# ---------------------- HELPERS ----------------------
def enqueue_output(out, log_queue):
    """Read output from subprocess and push to queue"""
    for line in iter(out.readline, b''):
        text = line.decode('utf-8', errors="ignore").strip()
        if text:
            log_queue.put(text)
    out.close()


def start_detection_process(script_name, process_var_name, log_queue):
    """Start a subprocess for a detection script"""
    global_vars = globals()
    proc = global_vars.get(process_var_name)
    if proc is not None and proc.poll() is None:
        return False  # already running

    # ✅ Always use the Python from current venv
    python_exec = sys.executable
    print(f"[DEBUG] Using Python: {python_exec}")  # Debug log

    # ✅ Run script from its own directory
    script_path = os.path.abspath(script_name)
    script_dir = os.path.dirname(script_path)

    proc = subprocess.Popen(
        [python_exec, "-u", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=script_dir,
        env=os.environ.copy()  # inherit venv env
    )
    global_vars[process_var_name] = proc

    # Start thread to capture logs
    threading.Thread(
        target=enqueue_output, args=(proc.stdout, log_queue), daemon=True
    ).start()

    return True


def stop_detection_process(process_var_name):
    """Stop subprocess if running"""
    global_vars = globals()
    proc = global_vars.get(process_var_name)
    if proc and proc.poll() is None:
        proc.terminate()
        global_vars[process_var_name] = None
        return True
    return False


def generate_logs(log_queue):
    """Stream subprocess logs to browser via SSE"""
    def generate():
        while True:
            try:
                line = log_queue.get(timeout=0.5)
                yield f"data: {line}\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"
    return Response(stream_with_context(generate()), mimetype="text/event-stream")


# ---------------------- ROUTES ----------------------

@admin_bp.route("/admin/detection_control")
def detection_control():
    return render_template("admin_detection_control.html")


# Criminal detection routes
@admin_bp.route("/admin/start_criminal_detection")
def start_criminal_detection():
    started = start_detection_process("detector.py", "criminal_process", criminal_log_queue)
    if started:
        return jsonify(ok=True, message="Criminal detection started.")
    return jsonify(ok=False, message="Criminal detection already running.")


@admin_bp.route("/admin/stop_criminal_detection")
def stop_criminal_detection():
    stopped = stop_detection_process("criminal_process")
    if stopped:
        return jsonify(ok=True, message="Criminal detection stopped.")
    return jsonify(ok=False, message="Criminal detection was not running.")


@admin_bp.route("/admin/criminal_detection_logs")
def criminal_detection_logs():
    return generate_logs(criminal_log_queue)


# Weapon detection routes
@admin_bp.route("/admin/start_weapon_detection")
def start_weapon_detection():
    started = start_detection_process("gun_webcam_test.py", "weapon_process", weapon_log_queue)
    if started:
        return jsonify(ok=True, message="Weapon detection started.")
    return jsonify(ok=False, message="Weapon detection already running.")


@admin_bp.route("/admin/stop_weapon_detection")
def stop_weapon_detection():
    stopped = stop_detection_process("weapon_process")
    if stopped:
        return jsonify(ok=True, message="Weapon detection stopped.")
    return jsonify(ok=False, message="Weapon detection was not running.")


@admin_bp.route("/admin/weapon_detection_logs")
def weapon_detection_logs():
    return generate_logs(weapon_log_queue)


# Violence detection routes
@admin_bp.route("/admin/start_violence_detection")
def start_violence_detection():
    started = start_detection_process("violence_detect.py", "violence_process", violence_log_queue)
    if started:
        return jsonify(ok=True, message="Violence detection started.")
    return jsonify(ok=False, message="Violence detection already running.")


@admin_bp.route("/admin/stop_violence_detection")
def stop_violence_detection():
    stopped = stop_detection_process("violence_process")
    if stopped:
        return jsonify(ok=True, message="Violence detection stopped.")
    return jsonify(ok=False, message="Violence detection was not running.")


@admin_bp.route("/admin/violence_detection_logs")
def violence_detection_logs():
    return generate_logs(violence_log_queue)
