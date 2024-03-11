import asyncio
import google.generativeai as genai
from time import sleep
from PIL import Image

from search import search
from voice import record_and_transcribe
from webcam import cam, take_pic
from tts import tts
import azurespeech
from prompts import prompts
from button import start_monitoring
from gemini import model, conv

from dotenv import load_dotenv
from os import getenv

from setup_logging import logger

load_dotenv()

GEMINI: str = getenv("GEMINI")
genai.configure(api_key=GEMINI)

# don't want error due to 'safety' from gemini
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

# model = genai.GenerativeModel("gemini-pro", safety_settings=safety_settings)


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
    global model

    model.use_vision()

    pic_relevance = await model.prompt("pic_relevance", pic, question=question)
    pic_relevance = pic_relevance.text.lower()

    print(f"{pic_relevance=}")

    pic = pic if "no" not in pic_relevance else None

    model.choose_model_from(pic)

    logger.debug(f"Checking to search for '{question}'")
    to_search = await model.prompt("to_search", pic, question=question)

    to_search = to_search.text
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

    logger.debug("Generating final response")
    final_response = model.prompt_sync(final_message, pic, **params)
    logger.debug("Final response generated")
    print()

    # async for chunk in final_response:
    #     print(chunk.text, end="")

    # queue.put(final_response.text)
    print(final_response.parts)
    print("-----")
    print(final_response.text)

    azurespeech.text_to_speech(final_response.text.replace("**", ""))

    print()
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


loop = asyncio.new_event_loop()
start_monitoring()

try:
    record_and_transcribe(main, loop=loop)
except KeyboardInterrupt:
    logger.debug("Ctrl+C detected, exiting...")
    print("Exiting...")

# closing the program
cam.close()
loop.run_until_complete(shutdown(loop))
logger.info("Exited")
