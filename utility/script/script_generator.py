import os
from openai import OpenAI
import json

if len(os.environ.get("GROQ_API_KEY", "")) > 30:
    from groq import Groq
    model = "mixtral-8x7b-32768"
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
else:
    OPENAI_API_KEY = os.getenv('OPENAI_KEY')
    model = "gpt-4o"
    client = OpenAI(api_key=OPENAI_API_KEY)

def generate_script(article_content):
    """
    Generate a script for a video by summarizing the given article content.

    Parameters:
        article_content (str): The content of the article to summarize.

    Returns:
        str: The generated script.
    """
    prompt = (
        """You are a seasoned content writer for a YouTube Shorts channel, specializing in facts videos. 
        Your task is to summarize an article to create a concise and engaging script. The script should be less than 140 words, 
        fitting into a 50-second video.

        Provide the output in a JSON format strictly as below:

        {"script": "Here is the script ..."}

        Here is the article content to summarize:
        {article_content}
        """
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": article_content}
        ]
    )

    content = response.choices[0].message.content
    try:
        script = json.loads(content)["script"]
    except Exception as e:
        json_start_index = content.find('{')
        json_end_index = content.rfind('}')
        content = content[json_start_index:json_end_index + 1]
        script = json.loads(content)["script"]

    return script
