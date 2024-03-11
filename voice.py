import pyaudio
import asyncio
from typing import Callable, Awaitable
import speech_recognition as sr
import pvporcupine as pv
import struct

import sounds
import azurespeech
import webcam
import button

from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Initialize recognizer
recognizer = sr.Recognizer()
porcupine = pv.create(access_key=getenv("PORCUPINE"), keywords=["jarvis"])


def record_and_transcribe(
    coro: Callable[[str], Awaitable] = None, loop: asyncio.AbstractEventLoop = None
):
    """
    Main function to listen and transcribe the speech.

    Args:
        coro (Callable[[str], Awaitable], optional): Function to run. Defaults to None.
        loop (asyncio.AbstractEventLoop, optional): Loop to use. Defaults to None.
    """
    pa = pyaudio.PyAudio()
    chosen_device_index = -1
    for x in range(0, pa.get_device_count()):
        info = pa.get_device_info_by_index(x)
        if info["name"] == "pulse":
            chosen_device_index = info["index"]
            break
    p = pyaudio.PyAudio()
    stream = p.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length,
        input_device_index=chosen_device_index,
    )

    # Adjust for ambient noise and record audio
    print("Adjusting for ambient noise...")
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, 3)

    print("I am ready to record after you say 'Jarvis'. Say 'Jarvis' to activate.")

    try:
        while True:
            if not button.button_pressed:
                pcm = stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                # Check if the wake word is detected
                wake_word_heard = porcupine.process(pcm) >= 0

                if not wake_word_heard:
                    continue

                print("Wake word 'Jarvis' heard")
            else:
                button.button_pressed = False
                print("Button pressed")

            sounds.wake_word_detected()
            pic = webcam.take_pic()

            print("\nListening for speech...")
            text = azurespeech.speech_to_text()
            if text is None:
                print("No speech detected within timeout period.")
                continue
            print("Transcription: " + text)

            sounds.stt()

            if coro is not None:
                if loop is None:
                    asyncio.run(coro(text, pic))
                else:
                    loop.run_until_complete(coro(text, pic))
    except KeyboardInterrupt:
        print("Exiting...")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()
