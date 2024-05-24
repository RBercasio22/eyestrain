from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
from threading import Thread
import numpy as np
import imutils
import time
import dlib
import cv2
import threading
import pyrebase
import json


# firebase Configuration for web application to mobile app
config = {
    "apiKey": "AIzaSyCWl5-CwN2NYh_RZm1-P1O0l99Ete26Je0",
    "authDomain": "example.com",
    "databaseURL": "https://example.com",
    "storageBucket": "example.com",
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

from checkInternet import *
from playAlarm import *
from gps import *

location = 0
speed = 0
alarm_val = 0
status_val = "NOT_FOUND"

while location == 0:
    location, speed = getLocation()
    

def multiple_uploads():
    try:
     with open("data.txt", "r") as file:
      for line in file:
       data = json.loads(line)
       db.child("updates").push(data)
     return 1
    except Exception as e:
     return 0


def save_send_data():
    date_now, time_now = getDateTime()
    location, speed = getLocation()
    data = {"date": date_now, "time": time_now, "gps": location, "speed": speed, "alarm": alarm_val, "status": status_val}
    
    if not connected():
     with open("data.txt", "a") as file:
      json.dump(data, file)
      file.write("\n")
      print("Save data to file")
    
    else:
     try:
      # all data.txt must be uploaded
      mult_data = multiple_uploads()
      if mult_data == 1:
       response = db.child("updates").push(data)
       with open("data.txt", "w") as file:
        pass
       print("Upload data (Multiple): ", response)
      else:
       response = db.child("updates").push(data)
       print("Upload data: ", response)
    
     except Exception as e:
      print("Error updating firebase: ", e)
      with open("data.txt", "a") as file:
       json.dump(data, file)
       file.write("\n")
       print("Save data to file")

    if speed > 80:
     alarm_on()
     playAlarm()
    
def schedule_function(interval):
    global location
    global speed
    t = threading.Timer(interval, schedule_function, args=[interval])
    t.start()
    save_send_data()
    
interval = 30
schedule_function(interval)

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear


predictor_file = "shape_predictor_68_face_landmarks.dat"

EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 80
COUNTER = 0
HIGH_EAR_COUNTER = 0
ALARM_ON = False
AWAY_COUNTER = 0
AWAY_SENT = False

print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_file)
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
print("[INFO] starting video stream thread...")
vs = VideoStream(0).start()
vs.stream.set(3, 640)
vs.stream.set(4, 480)
time.sleep(1.0)

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)

    if not rects:
        if AWAY_COUNTER % 50 == 0 or AWAY_COUNTER == 0:
            print(f"AWAY: {AWAY_COUNTER}")
        AWAY_COUNTER += 1
        if AWAY_COUNTER > 100:
            if not AWAY_SENT:
                AWAY_SENT = True
                status_val = "NOT_FOUND"
                print("NOT_FOUND")
                save_send_data()

    else:
        if AWAY_SENT:
            status_val = "NORMAL"
            print("NORMAL")
            save_send_data()
            COUNTER = 0
            AWAY_SENT = False
        AWAY_COUNTER = 0

    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0
        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

        print(f"counter: {COUNTER}")
        print(f"high c : {HIGH_EAR_COUNTER}")
        if ear < EYE_AR_THRESH:
            COUNTER += 1
            if COUNTER >= EYE_AR_CONSEC_FRAMES:
                alarm_val = 1
                save_send_data()
                alarm_on()
                playAlarm()
                COUNTER = 0
            else:
                alarm_val = 0
        else:
            if HIGH_EAR_COUNTER > 10:
                COUNTER = 0
            else:
                HIGH_EAR_COUNTER += 1


    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cv2.destroyAllWindows()
vs.stop()
