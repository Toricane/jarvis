prompts = dict(
    pic_relevance="""
I have a question: {question}

Is the picture relevant to my question?

Task:
Respond with "yes" if the picture is relevant to my question.
Respond with "no" otherwise.
No other output is needed.
""",
    to_search="""
I have a question: {question}

I can search the internet and provide you search results to help you answer the question.
I want to know whether or not you can answer the question accurately and precisely with the information you already have, without me providing you my search results.
For example, if the question is asking with relevant information in an attached photo, then you don't need to search unless you want to search for object names from the photo.
If it's something conversational, such as "Hello" or something similar, then you don't need to search the internet.
Use your common sense to see whether you can answer my question without search results.

Task:
Respond with "yes" if you can answer my question without needing my internet search results with accuracy and precision.
Respond with "no" if you need my internet search results to answer my question with accuracy and precision.
""",
    final_prompts=dict(
        no_search="""
I have a question: {question}

I want you to answer the question to the best of your abilities.
Keep your answer to the question concise. The plan is that it will be converted from text to speech and spoken to the user. Keep it under 200 words.
""",
        yes_search="""
I have a question: {question}

I want you to answer the question using the following search results.
Keep your answer to the question concise. The plan is that it will be converted from text to speech and spoken to the user. Keep it under 200 words.
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

If you can answer my question with accuracy and precision, respond with "Yes."
If you cannot answer my question, but you want more information from a good search result, respond with "More information from website <number of the website>."
If you think the search results are not helpful, respond with "No."
""",
    ),
    _internal=dict(),
)

print(
    prompts["pic_relevance"].strip().format(question="What is the capital of France?")
)
