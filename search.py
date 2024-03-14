import aiohttp
from bs4 import BeautifulSoup
import json
import asyncio
import google.generativeai as genai
from pprint import pprint
from PIL import Image
from prompts import prompts
from ai import Model

from dotenv import load_dotenv
from os import getenv

load_dotenv()

GOOGLE_SEARCH: str = getenv("GOOGLE_SEARCH")


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    """
    Fetches the content of a webpage.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        url (str): The URL of the webpage to fetch.

    Returns:
        str: The content of the webpage.
    """
    try:
        async with session.get(url) as response:
            return await response.text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print("ERROR", url, e)
        return ""


async def search_with_serper(query: str):
    url = "https://google.serper.dev/search"
    payload = json.dumps(
        {
            "q": query,
            "num": 10,
        }
    )
    headers = {"X-API-KEY": GOOGLE_SEARCH, "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=payload, timeout=5
        ) as response:
            json_content = await response.json()
            return json_content


async def search_google(query: str):
    """
    Search with serper and return the contexts.
    """
    json_content = await search_with_serper(query)
    try:
        contexts = []
        if json_content.get("knowledgeGraph"):
            url = json_content["knowledgeGraph"].get("descriptionUrl") or json_content[
                "knowledgeGraph"
            ].get("website")
            snippet = json_content["knowledgeGraph"].get("description")
            if url and snippet:
                contexts.append(
                    {
                        "name": json_content["knowledgeGraph"].get("title", ""),
                        "url": url,
                        "snippet": snippet,
                    }
                )
        if json_content.get("answerBox"):
            url = json_content["answerBox"].get("url")
            snippet = json_content["answerBox"].get("snippet") or json_content[
                "answerBox"
            ].get("answer")
            if url and snippet:
                contexts.append(
                    {
                        "name": json_content["answerBox"].get("title", ""),
                        "url": url,
                        "snippet": snippet,
                    }
                )
        contexts += [
            {"name": c["title"], "url": c["link"], "snippet": c.get("snippet", "")}
            for c in json_content["organic"]
        ]

        return contexts[:8]
    except KeyError:
        return []


# asyncio.run(search_google("What is the capital of France?"))


async def get_main_content(url: str) -> str:
    """
    Get the main content of a webpage.

    Args:
        url (str): The URL of the webpage to get the main content from.

    Returns:
        str: The main content of the webpage.
    """
    print("Fetching text", end=" - ")
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        html = await fetch(session, url)
        soup = BeautifulSoup(html, "lxml")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text
        text = soup.get_text(separator="\n", strip=True)

        print("Done fetching text", end=" - ")
        return text


filters = {
    "404 Not Found",
    "Not Found\nPage not foundThe page you are looking for doesn't exist or has been moved.",
}


async def cleanup(question: str, text: str, model: Model, pic) -> str:
    """
    Cleans up the text and only sends the important text relating to the question.

    Args:
        question (str): The question.
        text (str): The text to clean up.
        model (genai.GenerativeModel): The GenerativeModel instance to use for generating content.

    Returns:
        str: The cleaned up text.
    """

    print("Clean up", end=" - ")
    message = "[search][cleanup]"

    try:
        response = await model.prompt(message, pic, question=question, text=text)
    except Exception as e:
        print("ERROR", e)
        return

    print("Done cleaning up", end=" - ")

    return response


async def search(
    question: str, model: Model, pic: Image.Image | None
) -> tuple[str, list[dict[str, str]]] | tuple[None, None]:
    """
    Searches Google for the given question and returns the search results.

    Args:
        question (str): The question to search Google for.
        model (genai.GenerativeModel): The GenerativeModel instance to use for generating content.

    Returns:
        tuple[str, list[dict[str, str]]] | tuple[None, None]: The formatted search results and the search results.
    """

    if pic is not None:
        prompt = "[search][search_query_img]"
    else:
        prompt = "[search][search_query]"

    search_query = await model.prompt(prompt, pic, question=question)
    print("Search query:", search_query)
    print()

    # search google
    results: list[dict[str, str]] = await search_google(search_query)
    """
    results = [
        {
            "name": "Title of the search result",
            "snippet": "Snippet of the search result",
            "url": "URL of the search result"
        }, ...
    ]
    """
    formatted_results = "\n".join(
        [
            f"{i}: {r['name']}\n{r['url']}\n{r['snippet']}\n"
            for i, r in enumerate(results, 1)
        ]
    )

    prompt = "[search][followup]"

    response = await model.prompt(
        prompt, pic, question=question, formatted_results=formatted_results
    )

    if "yes" in response.lower():
        print("Yes")
    elif "more information" in response.lower():
        print("More information")
        print(response)
        web_num = [
            num
            for num in range(1, 11)
            if str(num) in response.split("\n")[0].split()[-1]
        ][0] - 1
        url = results[web_num]["url"]
        content = await get_main_content(url)
        cleaned_content = await cleanup(question, content, model, pic)
        results[web_num]["content"] = cleaned_content
        n = "\n"
        formatted_results = "\n".join(
            [
                f"{i}: {r['name']}\n{r['url']}\n{r['snippet']}\n{r.get('content', '')}{n if r.get('content', '') else ''}"
                for i, r in enumerate(results, 1)
            ]
        )
    else:
        print("No")
        return None, None
    print("\n\nSearch results:")
    print("--------------------------------------------------")
    try:
        print(formatted_results)
    except Exception:
        if formatted_results:
            formatted_results_copy = formatted_results.encode("utf-8")
        print(formatted_results_copy)
    print("--------------------------------------------------")
    return formatted_results, results
