import playsound
# pip install playsound==1.2.2
import pyrebase
import threading
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)

config = {
    "apiKey": "AIzaSyCWl5-CwN2NYh_RZm1-P1O0l99Ete2pJe0",
    "authDomain": "eyeblinker-status.firebaseapp.com",
    "databaseURL": "https://eyeblinker-status-default-rtdb.firebaseio.com",
    "storageBucket": "eyeblinker-status.appspot.com",
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

alarm_file = "alarmFile.mp3"
alarm_on_flag = False

def alarm_on():
    global alarm_on_flag
    alarm_on_flag = True
    
def alarm_off():
    global alarm_on_flag
    alarm_on_flag = False

def function_one(stop_event):
    while not stop_event.is_set():
        playsound.playsound(alarm_file, block=True)


def function_two(stop_event):
    global alarm_on_flag
    while True:
        if alarm_on_flag:
            GPIO.output(23, GPIO.HIGH)
            GPIO.output(24, GPIO.HIGH)
        else:
            try:
                x = db.child("updates").child("alarm").get().val()
                if int(x) == 0:
                    GPIO.output(23, GPIO.LOW)
                    GPIO.output(24, GPIO.LOW)
                    break
            except Exception as e:
                GPIO.output(23, GPIO.LOW)
                GPIO.output(24, GPIO.LOW)
    stop_event.set()


def playAlarm():
    stop_flag = threading.Event()

    thread_one = threading.Thread(target=function_one, args=(stop_flag,))
    thread_two = threading.Thread(target=function_two, args=(stop_flag,))

    thread_one.start()
    thread_two.start()

    thread_one.join()
