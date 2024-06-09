prompts = dict(
    pic_relevance="""
I have a question: {question}

You are seeing what I'm looking at. Is what I'm seeing relevant to my question?
If I am asking along the lines of "What is this?" or "What is in front of me?" or "Describe what you see" or "See this" or "In front of me," then you should respond with "Yes."

Task:
Respond with "Yes." if what I'm looking at is relevant to my question.
Respond with "No." otherwise.
""",
    to_search="""
I have a question: {question}

I can search the internet and provide you search results to help you answer the question.
I want to know whether or not you can answer the question accurately and precisely with the information you already have, without me providing you my search results.
For example, if the question is asking with relevant information in an attached photo, then you don't need to search unless you want to search for object names from the photo.
If it's something conversational, such as "Hello" or something similar, then you don't need to search the internet.
Use your common sense to see whether you can answer my question without search results.
Approximations are not preferred if I can search the web and give you information to answer the question with accuracy and precision.

Task:
Respond with "yes" if you can answer my question without needing my internet search results with accuracy and precision.
Respond with "no" if you need my internet search results to answer my question with accuracy and precision.
""",
    final_prompts=dict(
        no_search="""
I have a question: {question}

I want you to answer my question to the best of your abilities.
Keep your answer to my question concise. The plan is that it will be converted from text to speech and spoken to the user. Keep it under 200 words.
""",
        yes_search="""
I have a question: {question}

I want you to answer my question using the following search results.
Keep your answer to my question concise. The plan is that it will be converted from text to speech and spoken to the user. Keep it under 200 words.
If the search results have multiple dates/times, try to answer with the most recent and accurate data.
If you find that the search results are not helpful, you can answer it to the best of your ability.

Here are some search results that you can use to answer my question:
'''
{formatted_search_contents}
'''""",
    ),
    search=dict(
        cleanup="""
Please clean up the following text and only send the important text relating to this question: {question}

Text: '''
{text}
'''
""",
        search_query="""
I have a question: {question}

I want you to give me a search query that I can use to search Google to find more information about this question.
Just give it, don't prefix it with something like 'Search query:'.
Your response should be a single line with just the search query.
If my question is already a good search query, you can just respond back with the question.
""",
        search_query_img="""
I have a question: {question}

I want you to give me a search query that I can use to search Google to find more information about this question.
Just give it, don't prefix it with something like 'Search query:'.
Your response should be a single line with just the search query.
If my question is already a good search query, you can just respond back with the question.

I cannot search using the image. I can only search using text. If you cannot determine from the image, you can give me a search query which searches for object names or whatever.
""",
        followup="""
I have a question: {question}

I searched Google for the question and found the following search results:

'''
{formatted_results}
'''

If you think you need these search results to answer my question, respond with "Yes."
If you cannot answer my question, but you want more information from a good search result, respond with "<number of the website>: more information." For example, for website 1, "1: more information." Replace the number accordingly. No additional output is needed. I want only this 1 line of output.
If you think you don't need these search results for answering the question, respond with "No."
""",
    ),
    _internal=dict(),
)
