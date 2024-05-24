from gpiozero import Button
import time
import os

shut_But = Button(26)

while True:
    if shut_But.is_pressed:
        time.sleep(1)
        if shut_But.is_pressed:
            os.system("shutdown now -h")
            time.sleep(1)