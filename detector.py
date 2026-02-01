#before code



# import os
# import cv2
# import numpy as np
# import face_recognition
# from pymongo import MongoClient
# from playsound import playsound
# import threading
# from datetime import datetime
# import geocoder
#
# # ===== CONFIG =====
# MONGO_URI ="mongodb+srv://hattarakisarojani:user123@cluster0.np930bb.mongodb.net/crimson?retryWrites=true&w=majority&appName=Cluster0"
# DB_NAME = "crimson"
# COMPLAINTS_COLLECTION = "complaints"
#
# ALERT_SOUND = "alert.mp3"
# SAVE_DIR = os.path.join("static", "detectprof")
#
# # ===== CREATE SAVE FOLDER =====
# os.makedirs(SAVE_DIR, exist_ok=True)
#
# print("[INFO] Connecting to MongoDB...")
# client = MongoClient(MONGO_URI)
# db = client[DB_NAME]
# complaints = db[COMPLAINTS_COLLECTION]
#
# print("[INFO] Loading known criminal faces from MongoDB...")
# criminals = complaints.find({"status": "active"})
# known_face_encodings = []
# known_face_names = []
#
# for criminal in criminals:
#     name = criminal.get("name")
#     photo_path = criminal.get("photo")
#
#     if not photo_path:
#         continue
#
#     photo_path = os.path.normpath(photo_path)
#     full_path = os.path.join(os.getcwd(), photo_path)
#
#     if os.path.exists(full_path):
#         image = face_recognition.load_image_file(full_path)
#         encodings = face_recognition.face_encodings(image)
#         if encodings:
#             known_face_encodings.append(encodings[0])
#             known_face_names.append(name)
#             print(f"[INFO] Loaded: {name}")
#         else:
#             print(f"[WARNING] No face found in {full_path}")
#     else:
#         print(f"[WARNING] Image not found: {full_path}")
#
# if not known_face_encodings:
#     print("[ERROR] No criminal images loaded. Exiting.")
#     exit()
#
# # ===== ALERT SOUND =====
# def play_alert():
#     if os.path.exists(ALERT_SOUND):
#         threading.Thread(target=playsound, args=(ALERT_SOUND,), daemon=True).start()
#     else:
#         print(f"[WARNING] Alert sound '{ALERT_SOUND}' not found.")
#
# # ===== GET CURRENT LOCATION =====
# def get_current_location():
#     try:
#         g = geocoder.ip("me")  # get location based on IP
#         if g.ok:
#             lat, lng = g.latlng
#             return lat, lng
#     except Exception as e:
#         print(f"[WARNING] Could not fetch location: {e}")
#     return None, None
#
# # ===== SAVE DETECTION TO DB =====
# def save_detection(name, frame):
#     timestamp = datetime.now()
#     filename = f"{name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
#     file_path = os.path.join(SAVE_DIR, filename)
#     cv2.imwrite(file_path, frame)
#
#     # Get current location
#     lat, lng = get_current_location()
#     if not lat or not lng:
#         lat, lng = 0.0, 0.0  # fallback if location not found
#
#     # Find the active complaint for this name
#     complaint = complaints.find_one({"name": name, "status": "active"})
#     if not complaint:
#         print(f"[WARNING] No active complaint found for {name}, detection not saved.")
#         return
#     complaint_id = str(complaint.get("_id"))
#
#     detection_record = {
#         "complaint_id": complaint_id,
#         "name": name,
#         "photo": file_path.replace("\\", "/"),
#         "latitude": lat,
#         "longitude": lng,
#         "date": timestamp.strftime("%Y-%m-%d"),
#         "time": timestamp.strftime("%H:%M:%S")
#     }
#
#     # Prevent duplicate detection for the same complaint and time
#     for det in complaint.get("detections", []):
#         if det.get("date") == detection_record["date"] and det.get("time") == detection_record["time"]:
#             print(f"[INFO] Detection for complaint_id {complaint_id} at this time already exists. Skipping.")
#             return
#
#     result = complaints.update_one(
#         {"_id": complaint["_id"]},
#         {"$push": {"detections": detection_record}}
#     )
#     if result.modified_count > 0:
#         print(f"[DB] Detection appended for complaint_id {complaint_id} ({name}): {detection_record}")
#     else:
#         print(f"[WARNING] Could not append detection for complaint_id {complaint_id}.")
#
# print("[INFO] Starting webcam for detection...")
# video_capture = cv2.VideoCapture(0)
#
# while True:
#     ret, frame = video_capture.read()
#     if not ret:
#         break
#
#     small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
#     rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
#
#     face_locations = face_recognition.face_locations(rgb_small_frame)
#     face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
#
#     for face_encoding, face_location in zip(face_encodings, face_locations):
#         matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
#         face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
#
#         name = "Unknown"
#         if len(face_distances) > 0:
#             best_match_index = np.argmin(face_distances)
#             if matches[best_match_index]:
#                 name = known_face_names[best_match_index]
#
#         top, right, bottom, left = [v * 4 for v in face_location]
#         cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
#         cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
#
#         if name != "Unknown":
#             print(f"[ALERT] Criminal detected: {name}")
#             play_alert()
#             save_detection(name, frame)  # Save to DB and folder
#
#     cv2.imshow("Criminal Detection", frame)
#
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# video_capture.release()
# cv2.destroyAllWindows()




# only send mail when camera off
import os
import cv2
import numpy as np
import face_recognition
from pymongo import MongoClient
from playsound import playsound
import threading
from datetime import datetime
import geocoder
from flask import Flask
from flask_mail import Mail, Message

# ===== EMAIL CONFIG (Gmail SMTP) =====
EMAIL_USERNAME = os.getenv("MAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
EMAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("MAIL_PORT", 587))

# ===== Flask-Mail Setup =====
app = Flask(__name__)
app.config['MAIL_SERVER'] = EMAIL_SERVER
app.config['MAIL_PORT'] = EMAIL_PORT
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_USERNAME
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = EMAIL_USERNAME
mail = Mail(app)

# ===== MongoDB CONFIG =====
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "crimson"
COMPLAINTS_COLLECTION = "complaints"
USERS_COLLECTION = "users"

ALERT_SOUND = "alert.mp3"
SAVE_DIR = os.path.join("static", "detectprof")
os.makedirs(SAVE_DIR, exist_ok=True)

print("[INFO] Connecting to MongoDB...")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
complaints = db[COMPLAINTS_COLLECTION]
users = db[USERS_COLLECTION]

# ===== Load Known Criminals =====
print("[INFO] Loading known criminal faces from MongoDB...")
criminals = complaints.find({"status": "active"})
known_face_encodings = []
known_face_names = []

for criminal in criminals:
    name = criminal.get("name")
    photo_path = criminal.get("photo")

    if not photo_path:
        continue

    photo_path = os.path.normpath(photo_path)
    full_path = os.path.join(os.getcwd(), photo_path)

    if os.path.exists(full_path):
        image = face_recognition.load_image_file(full_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_face_encodings.append(encodings[0])
            known_face_names.append(name)
            print(f"[INFO] Loaded: {name}")
        else:
            print(f"[WARNING] No face found in {full_path}")
    else:
        print(f"[WARNING] Image not found: {full_path}")

if not known_face_encodings:
    print("[ERROR] No criminal images loaded. Exiting.")
    exit()

# ===== Alert Sound =====
def play_alert():
    if os.path.exists(ALERT_SOUND):
        threading.Thread(target=playsound, args=(ALERT_SOUND,), daemon=True).start()
    else:
        print(f"[WARNING] Alert sound '{ALERT_SOUND}' not found.")

# ===== Get Current Location =====
def get_current_location():
    try:
        g = geocoder.ip("me")
        if g.ok:
            lat, lng = g.latlng
            return lat, lng
    except Exception as e:
        print(f"[WARNING] Could not fetch location: {e}")
    return None, None

# ===== Save Detection =====
def save_detection(name, frame):
    timestamp = datetime.now()
    filename = f"{name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
    file_path = os.path.join(SAVE_DIR, filename)
    cv2.imwrite(file_path, frame)

    lat, lng = get_current_location()
    if not lat or not lng:
        lat, lng = 0.0, 0.0

    complaint = complaints.find_one({"name": name, "status": "active"})
    if not complaint:
        print(f"[WARNING] No active complaint found for {name}")
        return

    complaint_id = str(complaint.get("_id"))
    detection_record = {
        "complaint_id": complaint_id,
        "name": name,
        "photo": file_path.replace("\\", "/"),
        "latitude": lat,
        "longitude": lng,
        "date": timestamp.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H:%M:%S")
    }

    for det in complaint.get("detections", []):
        if det.get("date") == detection_record["date"] and det.get("time") == detection_record["time"]:
            print(f"[INFO] Duplicate detection for {name}. Skipping.")
            return

    result = complaints.update_one(
        {"_id": complaint["_id"]},
        {"$push": {"detections": detection_record}}
    )
    if result.modified_count > 0:
        print(f"[DB] Detection saved for {name}")
    else:
        print(f"[WARNING] Could not save detection for {name}")

# ===== Notify Admins via Email =====
def notify_admins_camera_off(detected_criminals):
    if not detected_criminals:
        print("[INFO] No criminals detected. Skipping email.")
        return

    print("[INFO] Sending camera-off notification to admins...")
    with app.app_context():
        admins = users.find({"role": "admin", "status": "approved"})

        for admin in admins:
            email = admin.get("email")
            full_name = admin.get("full_name", "Admin")

            detected_summary = "\n".join([f"- {name}: {count} times" for name, count in detected_criminals.items()])
            body = f"""
Hi {full_name},

The facial recognition camera was turned OFF.

Detected criminals during this session:
{detected_summary}

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Please review the detections in the dashboard.

- Crimson AI Surveillance System
            """.strip()

            try:
                msg = Message(
                    subject="🚨 Camera Turned OFF - Detections Recorded",
                    recipients=[email],
                    body=body
                )
                mail.send(msg)
                print(f"[MAIL] Sent to {email}")
            except Exception as e:
                print(f"[ERROR] Failed to send email to {email}: {e}")

# ===== Start Detection =====
print("[INFO] Starting webcam for detection...")
video_capture = cv2.VideoCapture(0)
detected_criminals = {}

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

        name = "Unknown"
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

        top, right, bottom, left = [v * 4 for v in face_location]
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        if name != "Unknown":
            print(f"[ALERT] Criminal detected: {name}")
            play_alert()
            save_detection(name, frame)
            detected_criminals[name] = detected_criminals.get(name, 0) + 1

    cv2.imshow("Criminal Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
notify_admins_camera_off(detected_criminals)



#
# import os
# import cv2
# import numpy as np
# import face_recognition
# from pymongo import MongoClient
# from playsound import playsound
# import threading
# from datetime import datetime
# import geocoder
# from flask import Flask
# from flask_mail import Mail, Message
#
# # ===== EMAIL CONFIG (Gmail SMTP) =====
# EMAIL_USERNAME = "hattarakisarojani@gmail.com"
# EMAIL_PASSWORD = "viyj ebaw vlmd tuxd"
# EMAIL_SERVER = "smtp.gmail.com"
# EMAIL_PORT = 587
#
# # ===== Flask-Mail Setup =====
# app = Flask(__name__)
# app.config['MAIL_SERVER'] = EMAIL_SERVER
# app.config['MAIL_PORT'] = EMAIL_PORT
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = EMAIL_USERNAME
# app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
# app.config['MAIL_DEFAULT_SENDER'] = EMAIL_USERNAME
# mail = Mail(app)
#
# # ===== MongoDB CONFIG =====
# MONGO_URI = "mongodb+srv://hattarakisarojani:user123@cluster0.np930bb.mongodb.net/crimson?retryWrites=true&w=majority&appName=Cluster0"
# DB_NAME = "crimson"
# COMPLAINTS_COLLECTION = "complaints"
# USERS_COLLECTION = "users"
#
# ALERT_SOUND = "alert.mp3"
# SAVE_DIR = os.path.join("static", "detectprof")
# os.makedirs(SAVE_DIR, exist_ok=True)
#
# print("[INFO] Connecting to MongoDB...")
# client = MongoClient(MONGO_URI)
# db = client[DB_NAME]
# complaints = db[COMPLAINTS_COLLECTION]
# users = db[USERS_COLLECTION]
#
# # ===== Load Known Criminals =====
# print("[INFO] Loading known criminal faces from MongoDB...")
# criminals = complaints.find({"status": "active"})
# known_face_encodings = []
# known_face_names = []
#
# for criminal in criminals:
#     name = criminal.get("name")
#     photo_path = criminal.get("photo")
#
#     if not photo_path:
#         continue
#
#     photo_path = os.path.normpath(photo_path)
#     full_path = os.path.join(os.getcwd(), photo_path)
#
#     if os.path.exists(full_path):
#         image = face_recognition.load_image_file(full_path)
#         encodings = face_recognition.face_encodings(image)
#         if encodings:
#             known_face_encodings.append(encodings[0])
#             known_face_names.append(name)
#             print(f"[INFO] Loaded: {name}")
#         else:
#             print(f"[WARNING] No face found in {full_path}")
#     else:
#         print(f"[WARNING] Image not found: {full_path}")
#
# if not known_face_encodings:
#     print("[ERROR] No criminal images loaded. Exiting.")
#     exit()
#
# # ===== Alert Sound =====
# def play_alert():
#     if os.path.exists(ALERT_SOUND):
#         threading.Thread(target=playsound, args=(ALERT_SOUND,), daemon=True).start()
#     else:
#         print(f"[WARNING] Alert sound '{ALERT_SOUND}' not found.")
#
# # ===== Get Current Location =====
# def get_current_location():
#     try:
#         g = geocoder.ip("me")
#         if g.ok:
#             lat, lng = g.latlng
#             return lat, lng
#     except Exception as e:
#         print(f"[WARNING] Could not fetch location: {e}")
#     return 0.0, 0.0
#
# # ===== Save Detection =====
# def save_detection(name, frame):
#     timestamp = datetime.now()
#     filename = f"{name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
#     file_path = os.path.join(SAVE_DIR, filename)
#     cv2.imwrite(file_path, frame)
#
#     lat, lng = get_current_location()
#     complaint = complaints.find_one({"name": name, "status": "active"})
#     if not complaint:
#         print(f"[WARNING] No active complaint found for {name}")
#         return file_path, lat, lng, timestamp
#
#     complaint_id = str(complaint.get("_id"))
#     detection_record = {
#         "complaint_id": complaint_id,
#         "name": name,
#         "photo": file_path.replace("\\", "/"),
#         "latitude": lat,
#         "longitude": lng,
#         "date": timestamp.strftime("%Y-%m-%d"),
#         "time": timestamp.strftime("%H:%M:%S")
#     }
#
#     for det in complaint.get("detections", []):
#         if det.get("date") == detection_record["date"] and det.get("time") == detection_record["time"]:
#             print(f"[INFO] Duplicate detection for {name}. Skipping.")
#             return file_path, lat, lng, timestamp
#
#     result = complaints.update_one(
#         {"_id": complaint["_id"]},
#         {"$push": {"detections": detection_record}}
#     )
#     if result.modified_count > 0:
#         print(f"[DB] Detection saved for {name}")
#     else:
#         print(f"[WARNING] Could not save detection for {name}")
#
#     return file_path, lat, lng, timestamp
#
# # ===== Notify Admins Immediately on Detection =====
# def notify_admins_detection(name, file_path, lat, lng, timestamp):
#     print(f"[INFO] Sending detection alert email for {name}...")
#
#     with app.app_context():
#         admins = users.find({"role": "admin", "status": "approved"})
#
#         for admin in admins:
#             email = admin.get("email")
#             full_name = admin.get("full_name", "Admin")
#
#             body = f"""
# Hi {full_name},
#
# Criminal detected: {name}
# Location: Latitude {lat}, Longitude {lng}
# Time: {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
# Saved Image: {file_path}
#
# Please take immediate action.
#
# - Crimson AI Surveillance System
#             """.strip()
#
#             try:
#                 msg = Message(
#                     subject=f" Criminal Detected: {name}",
#                     recipients=[email],
#                     body=body
#                 )
#                 mail.send(msg)
#                 print(f"[MAIL] Detection alert sent to {email}")
#             except Exception as e:
#                 print(f"[ERROR] Failed to send detection email to {email}: {e}")
#
# # ===== Notify Admins via Email (Camera Off) =====
# def notify_admins_camera_off(detected_criminals):
#     if not detected_criminals:
#         print("[INFO] No criminals detected. Skipping email.")
#         return
#
#     print("[INFO] Sending camera-off notification to admins...")
#     with app.app_context():
#         admins = users.find({"role": "admin", "status": "approved"})
#
#         for admin in admins:
#             email = admin.get("email")
#             full_name = admin.get("full_name", "Admin")
#
#             detected_summary = "\n".join([f"- {name}: {count} times" for name, count in detected_criminals.items()])
#             body = f"""
# Hi {full_name},
#
# The facial recognition camera was turned OFF.
#
# Detected criminals during this session:
# {detected_summary}
#
# Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#
# Please review the detections in the dashboard.
#
# - Crimson AI Surveillance System
#             """.strip()
#
#             try:
#                 msg = Message(
#                     subject="Camera Turned OFF - Detections Recorded",
#                     recipients=[email],
#                     body=body
#                 )
#                 mail.send(msg)
#                 print(f"[MAIL] Sent to {email}")
#             except Exception as e:
#                 print(f"[ERROR] Failed to send email to {email}: {e}")
#
# # ===== Start Detection =====
# print("[INFO] Starting webcam for detection...")
# video_capture = cv2.VideoCapture(0)
# detected_criminals = {}
#
# while True:
#     ret, frame = video_capture.read()
#     if not ret:
#         break
#
#     small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
#     rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
#
#     face_locations = face_recognition.face_locations(rgb_small_frame)
#     face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
#
#     for face_encoding, face_location in zip(face_encodings, face_locations):
#         matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
#         face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
#
#         name = "Unknown"
#         if len(face_distances) > 0:
#             best_match_index = np.argmin(face_distances)
#             if matches[best_match_index]:
#                 name = known_face_names[best_match_index]
#
#         top, right, bottom, left = [v * 4 for v in face_location]
#         cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
#         cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
#
#         if name != "Unknown":
#             print(f"[ALERT] Criminal detected: {name}")
#             play_alert()
#
#             # Save detection + send instant email
#             file_path, lat, lng, timestamp = save_detection(name, frame)
#             detected_criminals[name] = detected_criminals.get(name, 0) + 1
#             notify_admins_detection(name, file_path, lat, lng, timestamp)
#
#     cv2.imshow("Criminal Detection", frame)
#
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# video_capture.release()
# cv2.destroyAllWindows()
# notify_admins_camera_off(detected_criminals)
