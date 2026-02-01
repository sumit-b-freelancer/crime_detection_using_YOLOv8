from ultralytics import YOLO
import cv2
import threading
import pygame
import os
import datetime
from pymongo import MongoClient
import geocoder
from flask import Flask
from flask_mail import Mail, Message

# ============================
# MongoDB Connection
# ============================
client = MongoClient("mongodb+srv://hattarakisarojani:user123@cluster0.np930bb.mongodb.net/crimson?retryWrites=true&w=majority&appName=Cluster0")
db = client["crimson"]
weapon_collection = db["weapon_detection"]
users_collection = db["users"]

# ============================
# Email Config
# ============================
EMAIL_USERNAME = "hattarakisarojani@gmail.com"
EMAIL_PASSWORD = "viyj ebaw vlmd tuxd"
EMAIL_SERVER = "smtp.gmail.com"
EMAIL_PORT = 587

app = Flask(__name__)
app.config['MAIL_SERVER'] = EMAIL_SERVER
app.config['MAIL_PORT'] = EMAIL_PORT
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_USERNAME
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = EMAIL_USERNAME
mail = Mail(app)

# ============================
# Load YOLO Models
# ============================
model_gun = YOLO("best3.pt")          # Custom gun model
model_knife = YOLO("yolov8m.pt")      # Pre-trained knife detector

# ============================
# Setup Save Folder
# ============================
save_folder = os.path.join("static", "weaponprof")
os.makedirs(save_folder, exist_ok=True)

# ============================
# Sound Alert Setup
# ============================
pygame.mixer.init()
alert_sound = "alert.mp3"
playing_alert = False

def play_alert():
    global playing_alert
    playing_alert = True
    try:
        pygame.mixer.music.load(alert_sound)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue
    except Exception as e:
        print("Sound error:", e)
    playing_alert = False

# ============================
# Function to get location
# ============================
def get_location():
    try:
        g = geocoder.ip('me')
        if g.ok:
            return g.latlng  # [lat, lon]
    except Exception as e:
        print("Location fetch error:", e)
    return [None, None]

# ============================
# Store session detections
# ============================
session_detections = []

# ============================
# Start Webcam
# ============================
cap = cv2.VideoCapture(0)
print("[INFO] Press 'q' to quit weapon detection")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    detected_gun = False
    detected_knife = False
    weapon_type = None

    # ---- GUN Detection ----
    results_gun = model_gun.predict(source=frame, conf=0.4, verbose=False)[0]
    for box in results_gun.boxes:
        cls = int(box.cls[0])
        class_name = results_gun.names[cls]
        if "gun" in class_name.lower():
            detected_gun = True
            weapon_type = "Gun"
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, "Gun Detected", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            print("[Gun Model] Gun detected")

    # ---- KNIFE Detection ----
    results_knife = model_knife.predict(source=frame, conf=0.5, verbose=False)[0]
    for box in results_knife.boxes:
        cls = int(box.cls[0])
        class_name = results_knife.names[cls].lower()
        if class_name == "knife":
            detected_knife = True
            weapon_type = "Knife"
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, "Knife Detected", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            print("[Knife Model] Knife detected")

    # ============================
    # Save & Insert to MongoDB
    # ============================
    if (detected_gun or detected_knife):
        timestamp = datetime.datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M:%S")

        filename = f"{weapon_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = os.path.join(save_folder, filename)
        cv2.imwrite(file_path, frame)

        # Get location
        lat, lon = get_location()

        # Insert into MongoDB
        weapon_collection.insert_one({
            "profile_image": f"static/weaponprof/{filename}",
            "weapon_type": weapon_type,
            "location": {"latitude": lat, "longitude": lon},
            "time": time_str,
            "date": date_str
        })

        # Save in session for email
        session_detections.append({
            "weapon_type": weapon_type,
            "time": f"{date_str} {time_str}",
            "image": f"static/weaponprof/{filename}"
        })

    # ============================
    # Alert Sound
    # ============================
    if (detected_gun or detected_knife) and not playing_alert:
        threading.Thread(target=play_alert).start()

    # ============================
    # Display Video
    # ============================
    cv2.imshow("Gun & Knife Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# ============================
# Send email when camera stops
# ============================
def notify_admins(detections):
    if not detections:
        print("[INFO] No detections this session, skipping email.")
        return

    with app.app_context():
        admins = users_collection.find({"role": "admin", "status": "approved"})
        summary = "\n".join([f"- {d['weapon_type']} at {d['time']} (image: {d['image']})" for d in detections])

        for admin in admins:
            email = admin.get("email")
            name = admin.get("full_name", "Admin")
            body = f"""
Hi {name},

The weapon detection camera was turned OFF.

Here is the summary of weapons detected in this session:

{summary}

Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Please review the detections in the dashboard.

- Crimson AI Surveillance System
            """.strip()

            try:
                msg = Message(
                    subject="🚨 Camera Turned OFF - Weapon Detections Recorded",
                    recipients=[email],
                    body=body
                )
                mail.send(msg)
                print(f"[MAIL] Sent to {email}")
            except Exception as e:
                print(f"[ERROR] Failed to send email to {email}: {e}")

notify_admins(session_detections)






# here send eamil after detecting and when camera off both time
# from ultralytics import YOLO
# import cv2
# import threading
# import pygame
# import os
# import datetime
# from pymongo import MongoClient
# import geocoder
# from flask import Flask
# from flask_mail import Mail, Message
#
# # ============================
# # MongoDB Connection
# # ============================
# client = MongoClient("mongodb+srv://hattarakisarojani:user123@cluster0.np930bb.mongodb.net/crimson?retryWrites=true&w=majority&appName=Cluster0")
# db = client["crimson"]
# weapon_collection = db["weapon_detection"]
# users_collection = db["users"]
#
# # ============================
# # Email Config
# # ============================
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
# # ============================
# # Load YOLO Models
# # ============================
# model_gun = YOLO("best3.pt")          # Custom gun model
# model_knife = YOLO("yolov8m.pt")      # Pre-trained knife detector
#
# # ============================
# # Setup Save Folder
# # ============================
# save_folder = os.path.join("static", "weaponprof")
# os.makedirs(save_folder, exist_ok=True)
#
# # ============================
# # Sound Alert Setup
# # ============================
# pygame.mixer.init()
# alert_sound = "alert.mp3"
# playing_alert = False
#
# def play_alert():
#     global playing_alert
#     playing_alert = True
#     try:
#         pygame.mixer.music.load(alert_sound)
#         pygame.mixer.music.play()
#         while pygame.mixer.music.get_busy():
#             continue
#     except Exception as e:
#         print("Sound error:", e)
#     playing_alert = False
#
# # ============================
# # Function to get location
# # ============================
# def get_location():
#     try:
#         g = geocoder.ip('me')
#         if g.ok:
#             return g.latlng  # [lat, lon]
#     except Exception as e:
#         print("Location fetch error:", e)
#     return [None, None]
#
# # ============================
# # Notify Admins (Instant Detection)
# # ============================
# def notify_admins_detection(weapon_type, file_path, lat, lon, timestamp):
#     print(f"[INFO] Sending detection alert email for {weapon_type}...")
#
#     with app.app_context():
#         admins = users_collection.find({"role": "admin", "status": "approved"})
#
#         for admin in admins:
#             email = admin.get("email")
#             name = admin.get("full_name", "Admin")
#
#             body = f"""
# Hi {name},
#
# Weapon detected: {weapon_type}
# Location: Latitude {lat}, Longitude {lon}
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
#                     subject=f"Weapon Detected: {weapon_type}",
#                     recipients=[email],
#                     body=body
#                 )
#                 mail.send(msg)
#                 print(f"[MAIL] Detection alert sent to {email}")
#             except Exception as e:
#                 print(f"[ERROR] Failed to send detection email to {email}: {e}")
#
# # ============================
# # Store session detections
# # ============================
# session_detections = []
#
# # ============================
# # Start Webcam
# # ============================
# cap = cv2.VideoCapture(0)
# print("[INFO] Press 'q' to quit weapon detection")
#
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#
#     detected_gun = False
#     detected_knife = False
#     weapon_type = None
#
#     # ---- GUN Detection ----
#     results_gun = model_gun.predict(source=frame, conf=0.4, verbose=False)[0]
#     for box in results_gun.boxes:
#         cls = int(box.cls[0])
#         class_name = results_gun.names[cls]
#         if "gun" in class_name.lower():
#             detected_gun = True
#             weapon_type = "Gun"
#             x1, y1, x2, y2 = map(int, box.xyxy[0])
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
#             cv2.putText(frame, "Gun Detected", (x1, y1 - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
#             print("[Gun Model] Gun detected")
#
#     # ---- KNIFE Detection ----
#     results_knife = model_knife.predict(source=frame, conf=0.5, verbose=False)[0]
#     for box in results_knife.boxes:
#         cls = int(box.cls[0])
#         class_name = results_knife.names[cls].lower()
#         if class_name == "knife":
#             detected_knife = True
#             weapon_type = "Knife"
#             x1, y1, x2, y2 = map(int, box.xyxy[0])
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
#             cv2.putText(frame, "Knife Detected", (x1, y1 - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
#             print("[Knife Model] Knife detected")
#
#     # ============================
#     # Save & Insert to MongoDB
#     # ============================
#     if (detected_gun or detected_knife):
#         timestamp = datetime.datetime.now()
#         date_str = timestamp.strftime("%Y-%m-%d")
#         time_str = timestamp.strftime("%H:%M:%S")
#
#         filename = f"{weapon_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
#         file_path = os.path.join(save_folder, filename)
#         cv2.imwrite(file_path, frame)
#
#         # Get location
#         lat, lon = get_location()
#
#         # Insert into MongoDB
#         weapon_collection.insert_one({
#             "profile_image": f"static/weaponprof/{filename}",
#             "weapon_type": weapon_type,
#             "location": {"latitude": lat, "longitude": lon},
#             "time": time_str,
#             "date": date_str
#         })
#
#         # Save in session for summary email
#         session_detections.append({
#             "weapon_type": weapon_type,
#             "time": f"{date_str} {time_str}",
#             "image": f"static/weaponprof/{filename}"
#         })
#
#         # Send instant email alert
#         notify_admins_detection(weapon_type, f"static/weaponprof/{filename}", lat, lon, timestamp)
#
#     # ============================
#     # Alert Sound
#     # ============================
#     if (detected_gun or detected_knife) and not playing_alert:
#         threading.Thread(target=play_alert).start()
#
#     # ============================
#     # Display Video
#     # ============================
#     cv2.imshow("Gun & Knife Detection", frame)
#
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# cap.release()
# cv2.destroyAllWindows()
#
# # ============================
# # Send summary email when camera stops
# # ============================
# def notify_admins_summary(detections):
#     if not detections:
#         print("[INFO] No detections this session, skipping summary email.")
#         return
#
#     with app.app_context():
#         admins = users_collection.find({"role": "admin", "status": "approved"})
#         summary = "\n".join([f"- {d['weapon_type']} at {d['time']} (image: {d['image']})" for d in detections])
#
#         for admin in admins:
#             email = admin.get("email")
#             name = admin.get("full_name", "Admin")
#             body = f"""
# Hi {name},
#
# The weapon detection camera was turned OFF.
#
# Here is the summary of weapons detected in this session:
#
# {summary}
#
# Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#
# Please review the detections in the dashboard.
#
# - Crimson AI Surveillance System
#             """.strip()
#
#             try:
#                 msg = Message(
#                     subject="Camera Turned OFF - Weapon Detections Summary",
#                     recipients=[email],
#                     body=body
#                 )
#                 mail.send(msg)
#                 print(f"[MAIL] Summary sent to {email}")
#             except Exception as e:
#                 print(f"[ERROR] Failed to send summary email to {email}: {e}")
#
# notify_admins_summary(session_detections)
