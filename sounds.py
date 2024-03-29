from os import getcwd
from pathlib import Path
import pygame

pygame.mixer.init()
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
    play_sound("wake_word_detected")


def stt():
    play_sound("stt")


if __name__ == "__main__":
    from time import sleep

    play_sound("wake_word_detected")
    sleep(2)
    play_sound("stt")
    sleep(2)
    print("Done playing sounds")
