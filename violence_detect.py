# when camera is off that send mail

import cv2
import pygame
from model import Model
from datetime import datetime
import os
import pymongo
import time
import requests
from flask import Flask
from flask_mail import Mail, Message

# ---------------------------
# Email Config
# ---------------------------
import os
EMAIL_USERNAME = os.getenv("MAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
EMAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("MAIL_PORT", 587))

app = Flask(__name__)
app.config['MAIL_SERVER'] = EMAIL_SERVER
app.config['MAIL_PORT'] = EMAIL_PORT
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_USERNAME
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = EMAIL_USERNAME
mail = Mail(app)

# ---------------------------
# Function to Get Live Location
# ---------------------------
def get_location_from_ip():
    try:
        res = requests.get("https://ipinfo.io/json")
        data = res.json()
        lat, lng = map(float, data["loc"].split(","))
        return lat, lng
    except Exception as e:
        print(f"Could not get location: {e}")
        return None, None

# ---------------------------
# MongoDB Connection
# ---------------------------
try:
    mongo_uri = os.getenv("MONGO_URI")
    mongo_client = pymongo.MongoClient(mongo_uri)
    db = mongo_client["crimson"]
    violence_collection = db["violence_detections"]
    users_collection = db["users"]
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    exit()

# ---------------------------
# Paths
# ---------------------------
VIDEO_SAVE_DIR = "static/violenceprof"
os.makedirs(VIDEO_SAVE_DIR, exist_ok=True)

# ---------------------------
# Initialize model and sound
# ---------------------------
model = Model()
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("alert.mp3")

violence_keywords = ['fight', 'fire', 'violence', 'crash']

# ---------------------------
# Webcam
# ---------------------------
cap = cv2.VideoCapture(0)

fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 30
frame_time = 1 / fps

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = None
recording = False
record_start_time = None
record_duration = 5

last_time = time.time()
detected_events = []  # keep session detections

while True:
    ret, frame = cap.read()
    if not ret:
        print("No frame captured from camera.")
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = model.predict(image=rgb_frame)
    label = result['label']
    print(f"Predicted label: {label}")

    # Check if violence detected
    is_violence = None
    for keyword in violence_keywords:
        if keyword in label.lower():
            is_violence = keyword
            break

    if is_violence:
        print(f"Violence detected: {is_violence}")

        if not pygame.mixer.get_busy():
            alert_sound.play()

        if not recording:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"{timestamp}_{is_violence}.mp4"
            video_url = f"/static/violenceprof/{video_filename}"
            video_path = os.path.join(VIDEO_SAVE_DIR, video_filename)

            out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'avc1'),
                                  fps, (frame.shape[1], frame.shape[0]))
            recording = True
            record_start_time = time.time()

            now = datetime.now()
            lat, lng = get_location_from_ip()
            if lat is None or lng is None:
                lat, lng = 0.0, 0.0  # fallback

            try:
                result_insert = violence_collection.insert_one({
                    "video": video_url,
                    "violence_type": is_violence,
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "location": {"lat": lat, "lng": lng}
                })
                print(f"Inserted into DB with ID: {result_insert.inserted_id}")

                # Store for session email summary
                detected_events.append({
                    "violence_type": is_violence,
                    "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "video": video_url
                })

            except Exception as e:
                print(f"Failed to insert into DB: {e}")

        cv2.putText(frame, f"Prediction: {label}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), 8)

    else:
        print("No violence detected this frame.")
        cv2.putText(frame, f"Prediction: {label}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Save frames if recording
    if recording and out is not None:
        out.write(frame)
        if time.time() - record_start_time >= record_duration:
            recording = False
            out.release()
            out = None
            print(f"Recording stopped after {record_duration} seconds.")

    cv2.imshow("Violence Detection", frame)

    elapsed = time.time() - last_time
    if elapsed < frame_time:
        time.sleep(frame_time - elapsed)
    last_time = time.time()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if out is not None:
    out.release()
cv2.destroyAllWindows()

# ---------------------------
# Notify Admins when camera stops
# ---------------------------
def notify_admins(detected_events):
    if not detected_events:
        print("[INFO] No events detected this session. Skipping email.")
        return

    with app.app_context():
        admins = users_collection.find({"role": "admin", "status": "approved"})
        summary = "\n".join([f"- {e['violence_type']} at {e['time']} (video: {e['video']})"
                             for e in detected_events])

        for admin in admins:
            email = admin.get("email")
            name = admin.get("full_name", "Admin")
            body = f"""
Hi {name},

The violence detection camera was turned OFF.

Here is the summary of detected events this session:

{summary}

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Please check the dashboard for full details.

- Crimson AI Surveillance System
            """.strip()

            try:
                msg = Message(
                    subject=" Camera Turned OFF - Violence Events Recorded",
                    recipients=[email],
                    body=body
                )
                mail.send(msg)
                print(f"[MAIL] Sent to {email}")
            except Exception as e:
                print(f"[ERROR] Failed to send email to {email}: {e}")

notify_admins(detected_events)





# send mail when detect and camera off
#
#
#
# import cv2
# import pygame
# from model import Model
# from datetime import datetime
# import os
# import pymongo
# import time
# import requests
# from flask import Flask
# from flask_mail import Mail, Message
#
# # ---------------------------
# # Email Config
# # ---------------------------
# EMAIL_USERNAME = "hattarakisarojani@gmail.com"
# EMAIL_PASSWORD = "viyj ebaw vlmd tuxd"
# EMAIL_SERVER = "smtp.gmail.com"
# EMAIL_PORT = 587
#
# app = Flask(__name__)
# app.config['MAIL_SERVER'] = EMAIL_SERVER
# app.config['MAIL_PORT'] = EMAIL_PORT
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = EMAIL_USERNAME
# app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
# app.config['MAIL_DEFAULT_SENDER'] = EMAIL_USERNAME
# mail = Mail(app)
#
# # ---------------------------
# # Function to Get Live Location
# # ---------------------------
# def get_location_from_ip():
#     try:
#         res = requests.get("https://ipinfo.io/json")
#         data = res.json()
#         lat, lng = map(float, data["loc"].split(","))
#         return lat, lng
#     except Exception as e:
#         print(f"Could not get location: {e}")
#         return None, None
#
# # ---------------------------
# # MongoDB Connection
# # ---------------------------
# try:
#     mongo_client = pymongo.MongoClient(
#         "mongodb+srv://hattarakisarojani:user123@cluster0.np930bb.mongodb.net/crimson?retryWrites=true&w=majority&appName=Cluster0"
#     )
#     db = mongo_client["crimson"]
#     violence_collection = db["violence_detections"]
#     users_collection = db["users"]
#     print("Connected to MongoDB successfully.")
# except Exception as e:
#     print(f"MongoDB connection failed: {e}")
#     exit()
#
# # ---------------------------
# # Paths
# # ---------------------------
# VIDEO_SAVE_DIR = "static/violenceprof"
# os.makedirs(VIDEO_SAVE_DIR, exist_ok=True)
#
# # ---------------------------
# # Initialize model and sound
# # ---------------------------
# model = Model()
# pygame.mixer.init()
# alert_sound = pygame.mixer.Sound("alert.mp3")
#
# violence_keywords = ['fight', 'fire', 'violence', 'crash']
#
# # ---------------------------
# # Email Functions
# # ---------------------------
# def notify_admins_detection(event_type, video_url, lat, lng, timestamp):
#     """Send instant detection alert to admins."""
#     print(f"[INFO] Sending detection alert email for {event_type}...")
#
#     with app.app_context():
#         admins = users_collection.find({"role": "admin", "status": "approved"})
#         for admin in admins:
#             email = admin.get("email")
#             name = admin.get("full_name", "Admin")
#
#             body = f"""
# Hi {name},
#
# Violence detected: {event_type}
# Location: Latitude {lat}, Longitude {lng}
# Time: {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
# Saved Video: {video_url}
#
# Please take immediate action.
#
# - Crimson AI Surveillance System
#             """.strip()
#
#             try:
#                 msg = Message(
#                     subject=f" Violence Detected: {event_type}",
#                     recipients=[email],
#                     body=body
#                 )
#                 mail.send(msg)
#                 print(f"[MAIL] Detection alert sent to {email}")
#             except Exception as e:
#                 print(f"[ERROR] Failed to send detection email to {email}: {e}")
#
# def notify_admins_summary(detected_events):
#     """Send summary email when camera stops."""
#     if not detected_events:
#         print("[INFO] No events detected this session. Skipping email.")
#         return
#
#     with app.app_context():
#         admins = users_collection.find({"role": "admin", "status": "approved"})
#         summary = "\n".join([f"- {e['violence_type']} at {e['time']} (video: {e['video']})"
#                              for e in detected_events])
#
#         for admin in admins:
#             email = admin.get("email")
#             name = admin.get("full_name", "Admin")
#
#             body = f"""
# Hi {name},
#
# The violence detection camera was turned OFF.
#
# Here is the summary of detected events this session:
#
# {summary}
#
# Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#
# Please check the dashboard for full details.
#
# - Crimson AI Surveillance System
#             """.strip()
#
#             try:
#                 msg = Message(
#                     subject=" Camera Turned OFF - Violence Events Recorded",
#                     recipients=[email],
#                     body=body
#                 )
#                 mail.send(msg)
#                 print(f"[MAIL] Summary sent to {email}")
#             except Exception as e:
#                 print(f"[ERROR] Failed to send summary email to {email}: {e}")
#
# # ---------------------------
# # Webcam
# # ---------------------------
# cap = cv2.VideoCapture(0)
#
# fps = cap.get(cv2.CAP_PROP_FPS)
# if fps == 0:
#     fps = 30
# frame_time = 1 / fps
#
# fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# out = None
# recording = False
# record_start_time = None
# record_duration = 5
#
# last_time = time.time()
# detected_events = []  # keep session detections
#
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("No frame captured from camera.")
#         break
#
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     result = model.predict(image=rgb_frame)
#     label = result['label']
#     print(f"Predicted label: {label}")
#
#     # Check if violence detected
#     is_violence = None
#     for keyword in violence_keywords:
#         if keyword in label.lower():
#             is_violence = keyword
#             break
#
#     if is_violence:
#         print(f"Violence detected: {is_violence}")
#
#         if not pygame.mixer.get_busy():
#             alert_sound.play()
#
#         if not recording:
#             timestamp = datetime.now()
#             video_filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{is_violence}.mp4"
#             video_url = f"/static/violenceprof/{video_filename}"
#             video_path = os.path.join(VIDEO_SAVE_DIR, video_filename)
#
#             out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'avc1'),
#                                   fps, (frame.shape[1], frame.shape[0]))
#             recording = True
#             record_start_time = time.time()
#
#             lat, lng = get_location_from_ip()
#             if lat is None or lng is None:
#                 lat, lng = 0.0, 0.0  # fallback
#
#             try:
#                 result_insert = violence_collection.insert_one({
#                     "video": video_url,
#                     "violence_type": is_violence,
#                     "date": timestamp.strftime("%Y-%m-%d"),
#                     "time": timestamp.strftime("%H:%M:%S"),
#                     "location": {"lat": lat, "lng": lng}
#                 })
#                 print(f"Inserted into DB with ID: {result_insert.inserted_id}")
#
#                 # Store for session email summary
#                 detected_events.append({
#                     "violence_type": is_violence,
#                     "time": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
#                     "video": video_url
#                 })
#
#                 # Send instant detection email
#                 notify_admins_detection(is_violence, video_url, lat, lng, timestamp)
#
#             except Exception as e:
#                 print(f"Failed to insert into DB: {e}")
#
#         cv2.putText(frame, f"Prediction: {label}", (10, 30),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
#         cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), 8)
#
#     else:
#         print("No violence detected this frame.")
#         cv2.putText(frame, f"Prediction: {label}", (10, 30),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#
#     # Save frames if recording
#     if recording and out is not None:
#         out.write(frame)
#         if time.time() - record_start_time >= record_duration:
#             recording = False
#             out.release()
#             out = None
#             print(f"Recording stopped after {record_duration} seconds.")
#
#     cv2.imshow("Violence Detection", frame)
#
#     elapsed = time.time() - last_time
#     if elapsed < frame_time:
#         time.sleep(frame_time - elapsed)
#     last_time = time.time()
#
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# cap.release()
# if out is not None:
#     out.release()
# cv2.destroyAllWindows()
#
# # ---------------------------
# # Send Summary Email
# # ---------------------------
# notify_admins_summary(detected_events)
