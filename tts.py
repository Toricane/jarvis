"""
Windows local text to speech.
"""

import pyttsx3
import platform

engine = pyttsx3.init()
voices: list[pyttsx3.voice.Voice] = engine.getProperty("voices")

if platform.system() == "Windows":
    engine.setProperty("voice", voices[0].id)
else:
    engine.setProperty("voice", voices[17].id)


def tts(text: str) -> None:
    """
    Text to speech.

    Args:
        text (str): The text to speak.
    """
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    for i, voice in enumerate(voices):
        print(i, voice.id)
