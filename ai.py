import google.generativeai as genai
from google.api_core.exceptions import InternalServerError
from groq import Groq
from enum import Enum
from PIL import Image
from time import time

from prompts import prompts
from context import get_context

from dotenv import load_dotenv
from os import getenv

load_dotenv()

GEMINI: str = getenv("GEMINI")
GROQ: str = getenv("GROQ")
genai.configure(api_key=GEMINI)

gemini_model = "gemini-1.5-flash"
groq_model = "llama3-70b-8192"

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
    AI = "ai"


class Message:
    """A message in the conversation."""

    def __init__(self, type: Role, text: str) -> None:
        self.type = type
        self.text = text
        self.created_at: float = time()

    def json(self, model):  # TODO: typehint
        role = self.type.value
        if role != "user":
            role = "model" if isinstance(model, genai.GenerativeModel) else "assistant"
        if isinstance(model, genai.GenerativeModel):
            return {"role": role, "parts": [self.text]}
        else:
            return {"role": role, "content": self.text}


class Conversation:
    """A conversation between the user and the AI, with a list of Messages."""

    def __init__(self) -> None:
        self.messages: list[Message] = []
        self.last_user = Role.AI

    @property
    def history(self, model):  # TODO: typehint
        """Returns the formatted history of the conversation."""
        return [message.json(model) for message in self.messages]

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
        self.model: genai.GenerativeModel | Groq | None = None
        self.gemini_model: str = "gemini-1.5-flash"
        self.groq_model: str = "llama3-70b-8192"

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
            gemini_model, safety_settings=safety_settings
        )

    def use_text(self):
        """Sets the model to use the text model."""
        self.model = Groq(api_key=GROQ)

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

        prompt = prompt.strip().format(**kwargs)
        prompt += f"\n{get_context()}"

        return prompt

    async def prompt(
        self,
        prompt_key: str,
        pic: Image.Image = None,
        resolve: bool = True,
        **kwargs: str,
    ) -> str:
        """
        Asynchronously prompts the model.

        Args:
            prompt_key (str): The key of the prompt.
            pic (Image.Image, optional): The picture. Defaults to None.
            resolve (bool, optional): Whether to response.resolve(). Defaults to True.

        Returns:
            str: The response from the model.
        """
        prompt = self.get_prompt(prompt_key, **kwargs)

        if pic is not None:
            prompt = [pic, prompt]
            generation_config = None
            if prompt_key == "pic_relevance":
                generation_config = genai.types.GenerationConfig(
                    candidate_count=1,
                    stop_sequences=["."],
                    max_output_tokens=3,
                    temperature=0,
                )
            elif prompt_key == "[search][followup]":
                generation_config = genai.types.GenerationConfig(
                    candidate_count=1,
                    stop_sequences=["."],
                    max_output_tokens=10,
                    temperature=0,
                )

            try:
                response = await self.model.generate_content_async(
                    prompt, generation_config=generation_config
                )
            except InternalServerError as e:
                print("ERROR", e)
                print("Trying again...")
                response = await self.model.generate_content_async(
                    prompt, generation_config=generation_config
                )

            if resolve:
                await response.resolve()

            return response.text
        else:
            response = self.model.chat.completions.create(
                messages=[Message(Role.USER, prompt).json(self.model)], model=groq_model
            )
            return response.choices[0].message.content

    def prompt_sync(
        self,
        prompt_key: str,
        pic: Image.Image = None,
        resolve: bool = True,
        **kwargs: str,
    ) -> str:
        """
        Synchronously prompts the model.

        Args:
            prompt_key (str): The key of the prompt.
            pic (Image.Image, optional): The picture. Defaults to None.
            resolve (bool, optional): Whether to response.resolve(). Defaults to True.

        Returns:
            str: The response from the model.
        """
        prompt = self.get_prompt(prompt_key, **kwargs)

        if pic is not None:
            prompt = [pic, prompt]
            generation_config = None
            if prompt_key == "pic_relevance":
                generation_config = genai.types.GenerationConfig(
                    candidate_count=1, stop_sequences=["."], max_output_tokens=3
                )
            elif prompt_key == "[search][followup]":
                generation_config = genai.types.GenerationConfig(
                    candidate_count=1, stop_sequences=["."], max_output_tokens=10
                )

            try:
                response = self.model.generate_content(
                    prompt, generation_config=generation_config
                )
            except InternalServerError as e:
                print("ERROR", e)
                print("Trying again...")
                response = self.model.generate_content(
                    prompt, generation_config=generation_config
                )

            if resolve:
                response.resolve()

            return response.text
        else:
            response = self.model.chat.completions.create(
                messages=[Message(Role.USER, prompt).json(self.model)], model=groq_model
            )
            return response.choices[0].message.content


model = Model()
conv = Conversation()
