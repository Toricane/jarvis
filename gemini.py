import google.generativeai as genai
from enum import Enum
from PIL import Image
from time import time

from prompts import prompts

from dotenv import load_dotenv
from os import getenv

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


class Role(Enum):
    """The role of the author of the message."""

    USER = "user"
    AI = "model"


class Message:
    """A message in the conversation."""

    def __init__(self, type: Role, text: str) -> None:
        self.type = type
        self.text = text
        self.created_at: float = time()

    @property
    def json(self):
        return {"role": self.type.value, "parts": [self.text]}


class Conversation:
    """A conversation between the user and the AI, with a list of Messages."""

    def __init__(self) -> None:
        self.messages: list[Message] = []
        self.last_user = Role.AI

    @property
    def history(self):
        """Returns the formatted history of the conversation."""
        return [message.json for message in self.messages]

    def add(self, text: str) -> None:
        """
        Adds a new message to the conversation.

        Args:
            text (str): The text of the message.
        """
        self.last_user = Role.USER if self.last_user == Role.AI else Role.AI
        self.messages.append(Message(type=self.last_user, text=text))

    def refresh(self) -> None:
        """Deletes the history if the latest message is more than 10 minutes old."""
        if not self.messages:
            return

        latest_message = self.messages[-1]

        if time() - latest_message.created_at > 600:
            self.messages = []
            self.last_user = Role.AI


class Model:
    """A wrapper around the GenerativeModel from the gemini library."""

    def __init__(self) -> None:
        self.model: genai.GenerativeModel | None = None

    def choose_model_from(self, pic: Image.Image | None) -> None:
        """
        Chooses the model to use based on the presence of a picture.

        Args:
            pic (Image.Image | None): The picture.
        """
        if pic is None:
            self.use_text()
        else:
            self.use_vision()

    def use_vision(self):
        """Sets the model to use the vision model."""
        self.model = genai.GenerativeModel(
            "gemini-pro-vision", safety_settings=safety_settings
        )

    def use_text(self):
        """Sets the model to use the text model."""
        self.model = genai.GenerativeModel(
            "gemini-pro", safety_settings=safety_settings
        )

    @staticmethod
    def get_prompt(prompt_key: str, **kwargs: str) -> str:
        """
        Gets the prompt from the prompts file.

        Args:
            prompt_key (str): The key of the prompt.
            kwargs (str): The arguments to format the prompt with.

        Returns:
            str: The formatted prompt.
        """
        if "][" in prompt_key:
            group, key = prompt_key.split("][")
            group, key = group[1:], key[:-1]
            prompt = prompts[group][key]
        else:
            prompt = prompts[prompt_key]

        return prompt.strip().format(**kwargs)

    async def prompt(
        self,
        prompt_key: str,
        pic: Image.Image = None,
        resolve: bool = True,
        **kwargs: str
    ) -> genai.types.AsyncGenerateContentResponse:
        """
        Asynchronously prompts the model.

        Args:
            prompt_key (str): The key of the prompt.
            pic (Image.Image, optional): The picture. Defaults to None.
            resolve (bool, optional): Whether to response.resolve(). Defaults to True.

        Returns:
            genai.types.AsyncGenerateContentResponse: The response from the model.
        """
        prompt = self.get_prompt(prompt_key, **kwargs)

        if pic is not None:
            prompt = [prompt, pic]

        response = await self.model.generate_content_async(prompt)

        if resolve:
            await response.resolve()

        return response

    def prompt_sync(
        self,
        prompt_key: str,
        pic: Image.Image = None,
        resolve: bool = True,
        **kwargs: str
    ) -> genai.types.AsyncGenerateContentResponse:
        """
        Synchronously prompts the model.

        Args:
            prompt_key (str): The key of the prompt.
            pic (Image.Image, optional): The picture. Defaults to None.
            resolve (bool, optional): Whether to response.resolve(). Defaults to True.

        Returns:
            genai.types.AsyncGenerateContentResponse: The response from the model.
        """
        prompt = self.get_prompt(prompt_key, **kwargs)

        if pic is not None:
            prompt = [prompt, pic]

        response = self.model.generate_content(prompt)

        if resolve:
            response.resolve()

        return response


model = Model()
conv = Conversation()
