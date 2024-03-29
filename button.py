from gpiozero import Button
from time import time
import threading
from datetime import datetime

from webcam import take_pic
from sounds import play_sound

button = Button(2)
button_pressed = False
button_thread: threading.Thread | None = None


def monitor_button():
    global button_pressed

    while True:
        button.wait_for_press()
        press = time()
        button.wait_for_release()
        release = time()
        difference = release - press

        if difference > 3:
            print("shutting down")
            break

        if difference > 0.6:
            print("saving pic")
            play_sound("camera_shutter")
            pic = take_pic()
            pic.save(f"photos/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg")
            continue

        button_pressed = True

    # TODO: shutdown
    ...


def start_monitoring():
    global button_thread
    button_thread = threading.Thread(target=monitor_button, daemon=True)
    button_thread.start()
