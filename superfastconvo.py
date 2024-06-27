from typing import Callable
from time import sleep
import azurespeech

from os import getenv
from dotenv import load_dotenv
from groq import Groq
import threading
import button

from azurespeech import text_to_speech
from sounds import wake_word_detected, play_sound

load_dotenv()

USER_AGE = 16
USER_NAME = "Prajwal"
USER_PRONOUN = "he"
USER_INFO = "I like to build AI and computer programming projects and I like math."

AI_CHAT_STYLE = "Gen-Z"
AI_NAME = "Jarvis"

USER_INFO = USER_INFO.replace(" I like ", f" {USER_PRONOUN} likes ")
USER_INFO = USER_INFO.replace("I like ", f"{USER_PRONOUN.capitalize()} likes ")
USER_INFO = USER_INFO.replace("I am ", f"{USER_NAME} is ")
USER_INFO = USER_INFO.strip() + " "


class AI:
    def __init__(self) -> None:
        self.client: Groq = Groq(api_key=getenv("GROQ"))
        self.model = "llama3-70b-8192"
        self.talking: bool = False
        self.history: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    f"Your name is {AI_NAME} and you are a friend who chats with the user as if you were a person beside them. "
                    + "Your responses will be spoken out to the user. Be friendly and talk appropriately - "
                    + "format your messages as if you were speaking it, no additional formatting necessary. "
                    + "Don't be cringe. Don't glorify the user, he is your friend. "
                    + f"The user's name is {USER_NAME} and {USER_PRONOUN} is {USER_AGE} years old. "
                    + USER_INFO
                    + f"{USER_PRONOUN.capitalize()} wants to chat in a {AI_CHAT_STYLE} style. "
                    + "Don't say your name, the user already knows it. "
                    + 'One more thing, when ending the conversation, include the word "bye" in your response.'
                ),
            }
        ]

    def chat(self, text: str) -> str:
        self.history.append({"role": "user", "content": text})
        stream = self.client.chat.completions.create(
            messages=self.history, model=self.model, stream=True
        )

        response: str = ""
        full_response: str = ""
        thread = None

        print("AI: ", end="")
        # for chunk in stream:
        #     c: str = chunk.choices[0].delta.content
        #     if c:
        #         response += c
        #         print(c, end="")
        #         if thread is None:
        #             if any(c == x for x in (".", "?!", "!?", "!", "?", ":")):
        #                 full_response = response
        #                 response = response.strip()
        #                 thread = threading.Thread(
        #                     target=text_to_speech, args=(response,)
        #                 )
        #                 thread.start()
        #                 response = ""
        #         else:
        #             if (
        #                 any(c == x for x in (".", "?!", "!?", "!", "?", ":"))
        #                 and not thread.is_alive()
        #             ):
        #                 full_response += response
        #                 response = response.strip()
        #                 thread = threading.Thread(
        #                     target=text_to_speech, args=(response,)
        #                 )
        #                 thread.start()
        #                 response = ""
        for chunk in stream:
            c: str = chunk.choices[0].delta.content
            if c:
                response += c
                try:
                    print(c, end="")
                except UnicodeEncodeError:
                    print("UnicodeEncodeError")
                if thread is None:
                    base_endings = [".", "?!", "!?", "!", "?", ":"]
                    complete_endings = []
                    complete_endings.extend([f"{x} " for x in base_endings])
                    complete_endings.extend([f"{x}\n" for x in base_endings])
                    complete_endings.extend(base_endings)
                    for x in complete_endings:
                        if not x in response:
                            continue
                        response1, response = response.rsplit(x, 1)
                        response1 += x
                        full_response = response1
                        response1: str = response1.strip()
                        thread = threading.Thread(
                            target=text_to_speech, args=(response1,)
                        )
                        thread.start()

        if thread is not None:
            thread.join()

        full_response += response
        response = response.strip()

        azurespeech.ds = 0
        button.running = True
        text_to_speech(response)
        counter = 0

        while counter < 10:
            if azurespeech.ds == 0:
                counter += 1
            else:
                counter = 0
            sleep(0.1)

        azurespeech.ds = 0
        button.running = False

        # azurespeech.done_speaking = False

        if not full_response.strip():
            # TODO: find out why sometimes the response is empty
            print(stream.response)

        return full_response


def superfastconvo_record_and_transcribe():
    """Main function to listen and transcribe the speech."""
    ai = AI()
    sleep(1)
    wake_word_detected()
    try:
        while True:
            print("\n    Listening for speech...")
            text = azurespeech.speech_to_text()
            if text is None:
                print("    No speech detected within timeout period.")
                sleep(1)
                continue
            print("You: " + text)
            response = ai.chat(text)
            if any(
                c in response.lower()
                for c in (
                    "bye",
                    "see you later",
                    "take care",
                    "it was great chatting with you",
                    "it was nice chatting with you",
                    "catch you later",
                    "have a great day",
                    "later, ",
                )
            ):
                print("\n    Exiting...")
                play_sound("low_sound")
                break
    except KeyboardInterrupt:
        print("\n    Exiting...")
