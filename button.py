from gpiozero import Button
from time import time, sleep
import threading
from datetime import datetime

from webcam import take_pic
from sounds import play_sound, stt, camera_shutter, wake_word_detected
import azurespeech

import threading
import signal
import os

button = Button(2)
button_pressed = False
button_thread: threading.Thread | None = None

running: bool = False


def wait_for_button():
    button.wait_for_press()
    button.wait_for_release()
    print("Starting program...")
    wake_word_detected()


def monitor_button():
    global button_pressed

    while True:
        button.wait_for_press()
        press = time()
        button.wait_for_release()
        release = time()
        difference = release - press

        if running:
            azurespeech.speech_synthesizer.stop_speaking()
            azurespeech.speech_synthesizer.stop_speaking()
            azurespeech.speech_synthesizer.stop_speaking()
            continue
        else:
            button_pressed = True

        if difference > 0:
            print("shutting down")
            play_sound("low_sound")
            sleep(1)
            break

        if difference > 0.6:
            print("saving pic")
            play_sound("camera_shutter")
            pic = take_pic()
            pic.save(f"photos/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg")
            continue

    os.kill(os.getpid(), signal.SIGINT)


def start_monitoring():
    global button_thread
    button_thread = threading.Thread(target=monitor_button, daemon=True)
    button_thread.start()
