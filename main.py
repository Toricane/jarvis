from sounds import play_sound
from button import wait_for_button, start_monitoring

play_sound("low_sound")
wait_for_button()

import asyncio
import google.generativeai as genai
from time import sleep
from PIL import Image

from search import search
from voice import record_and_transcribe
from webcam import cam, take_pic
from tts import tts
import azurespeech
from azurespeech import text_to_speech
from prompts import prompts
from ai import model, conv, Message, Role
import button
import threading
from google.api_core.exceptions import InternalServerError
from superfastconvo import superfastconvo_record_and_transcribe

from setup_logging import logger

import signal


# Custom exception to indicate interruption from a thread
class ThreadKeyboardInterrupt(Exception):
    pass


def signal_handler(signum, frame):
    raise ThreadKeyboardInterrupt


signal.signal(signal.SIGINT, signal_handler)


async def shutdown(loop: asyncio.AbstractEventLoop):
    """
    Function to shutdown the async tasks and the event loop.

    Args:
        loop (asyncio.AbstractEventLoop): The loop to shutdown.
    """
    logger.debug("Shutting down async tasks...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]

    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


async def main(question: str, pic: Image.Image = None):
    """
    The main function which is run when JARVIS is activated.

    Args:
        question (str): The question from the user.
        pic (Image.Image, optional): The photo from the camera. Defaults to None.
    """
    logger.info("Main function running")
    # button.running = True
    global model

    model.use_vision()

    pic_relevance = await model.prompt("pic_relevance", pic, question=question)
    pic_relevance = pic_relevance.lower()

    print(f"{pic_relevance=}")

    pic = pic if "no" not in pic_relevance else None

    model.choose_model_from(pic)

    logger.debug(f"Checking to search for '{question}'")
    to_search = await model.prompt("to_search", pic, question=question)
    final_message = ""
    params: dict[str, str] = {"question": question}

    if "yes" in to_search.lower():
        logger.debug("No search")
        final_message = "[final_prompts][no_search]"
    elif "no" in to_search.lower():
        logger.debug("Search")
        formatted_search_contents, search_contents = await search(question, model, pic)

        if search_contents is None:
            final_message = "[final_prompts][no_search]"
        else:
            params["formatted_search_contents"] = formatted_search_contents
            final_message = "[final_prompts][yes_search]"

    # logger.debug("Generating final response")
    # final_response = model.prompt_sync(final_message, pic, **params)
    # logger.debug("Final response generated")
    # print()

    # # async for chunk in final_response:
    # #     print(chunk.text, end="")

    # # queue.put(final_response.text)
    # print(final_response.replace("**", ""))

    # azurespeech.text_to_speech(final_response.replace("**", ""))
    if pic is None:
        model.choose_model_from(pic)
        prompt = model.get_prompt(final_message, **params)
        stream = model.model.chat.completions.create(
            messages=[Message(Role.USER, prompt).json(model.model)],
            model=model.groq_model,
            stream=True,
        )

        response: str = ""
        full_response: str = ""
        thread = None

        print("AI: ", end="")
        for chunk in stream:
            c: str = chunk.choices[0].delta.content
            if c:
                response += c
                try:
                    print(c, end="")
                except UnicodeEncodeError:
                    print("UnicodeEncodeError")
                if thread is None:
                    if any(c == x or x in c for x in (".", "?!", "!?", "!", "?", ":")):
                        full_response = response
                        response = response.strip()
                        thread = threading.Thread(
                            target=text_to_speech, args=(response,)
                        )
                        thread.start()
                        response = ""
                else:
                    if (
                        any(c == x or x in c for x in (".", "?!", "!?", "!", "?", ":"))
                        and not thread.is_alive()
                    ):
                        full_response += response
                        response = response.strip()
                        thread = threading.Thread(
                            target=text_to_speech, args=(response,)
                        )
                        thread.start()
                        response = ""

        if thread is not None:
            thread.join()

        full_response += response
        response = response.strip()

        azurespeech.ds = 0
        button.running = True
        print("response: ", response)
        text_to_speech(response)
        counter = 0

        while counter < 10:
            if azurespeech.ds == 0:
                counter += 1
            else:
                counter = 0
            sleep(0.1)

        azurespeech.ds = 0

        # azurespeech.done_speaking = False

        if not full_response.strip():
            # TODO: find out why sometimes the response is empty
            print(stream.response)
    else:
        model.choose_model_from(pic)
        prompt = model.get_prompt(final_message, **params)
        prompt = [pic, prompt]

        try:
            stream = model.model.generate_content(prompt, stream=True)
        except InternalServerError as e:
            print("ERROR", e)
            print("Trying again...")
            stream = model.model.generate_content(prompt, stream=True)

        response: str = ""
        full_response: str = ""
        thread = None

        print("AI: ", end="")
        for chunk in stream:
            c: str = chunk.text
            if c:
                response += c
                try:
                    print(c, end="")
                except UnicodeEncodeError:
                    print("UnicodeEncodeError")
                if thread is None:
                    if any(c == x or x in c for x in (".", "?!", "!?", "!", "?", ":")):
                        full_response = response
                        response = response.strip()
                        thread = threading.Thread(
                            target=text_to_speech, args=(response,)
                        )
                        thread.start()
                        response = ""
                else:
                    if (
                        any(c == x or x in c for x in (".", "?!", "!?", "!", "?", ":"))
                        and not thread.is_alive()
                    ):
                        full_response += response
                        response = response.strip()
                        thread = threading.Thread(
                            target=text_to_speech, args=(response,)
                        )
                        thread.start()
                        response = ""

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

        # azurespeech.done_speaking = False

        if not full_response.strip():
            # TODO: find out why sometimes the response is empty
            print(stream.response)

    print()
    button.running = False
    logger.debug("Main function finished")


async def test(question: str, pic: Image.Image = None) -> None:
    """
    Testing function.

    Args:
        question (str): The question from the user.
        pic (Image.Image, optional): The photo from the camera. Defaults to None.
    """
    logger.debug("Testing...")
    ...


# wait_for_button()

loop = asyncio.new_event_loop()
start_monitoring()

try:
    record_and_transcribe(
        main, loop=loop, superfastconvojarvis=superfastconvo_record_and_transcribe
    )
except (KeyboardInterrupt, ThreadKeyboardInterrupt):
    logger.debug("Ctrl+C detected, exiting...")
    print("Exiting...")

# closing the program
cam.close()
loop.run_until_complete(shutdown(loop))
play_sound("low_sound")
sleep(1)
play_sound("low_sound")
sleep(1)
logger.info("Exited")
