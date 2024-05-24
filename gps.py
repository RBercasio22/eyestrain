import serial
import pynmea2
import datetime
import time
    
def getLocation():
    gps = ""
    port = "/dev/ttyAMA0"
    ser = serial.Serial(port, baudrate=9600, timeout=0.5)

    for i in range(10):
        ser.readline()
        time.sleep(0.1)

    while True:
     newdata = ser.readline().decode('ascii', errors='replace').strip()
      #print(f"gps: {newdata}")
      
     if newdata[0:6] == "$GPRMC":
      newmsg = pynmea2.parse(newdata)
      lat = newmsg.latitude
      lng = newmsg.longitude
      speed = newmsg.spd_over_grnd * 1.852  # Convert speed from knots to km/h

      latval = "{:.6f}".format(lat)
      lngval = "{:.6f}".format(lng)
      gps = f'"{str(latval)},{str(lngval)}"'
      print("location: ", gps)
      print("speed (km/h): ", speed)
      time.sleep(5)
      return gps, speed


def getDateTime():
    now = datetime.datetime.now()
    date = now.date()
    time = now.time()

    date_str = date.strftime("%Y-%m-%d")
    time_str = time.strftime("%H:%M:%S")
    return date_str, time_str
