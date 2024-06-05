from os import getcwd
from pathlib import Path
import pygame

try:
    pygame.mixer.init()
except pygame.error as e:
    print("Error initializing pygame mixer:", e)
current_dir = Path(getcwd())


def play_sound(file: str) -> None:
    """
    Play a sound file.

    Args:
        file (str): The name of the sound file to play.
    """
    sound_file_path = current_dir / "sounds" / f"{file}.wav"
    sound = pygame.mixer.Sound(str(sound_file_path))
    sound.play()


def wake_word_detected():
    play_sound("start_listening")


def stt():
    play_sound("finish_listening")


def camera_shutter():
    play_sound("camera_shutter")


if __name__ == "__main__":
    from time import sleep

    play_sound("start_listening")
    sleep(2)
    play_sound("finish_listening")
    sleep(2)
    print("Done playing sounds")
