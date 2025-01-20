import os
from openai import OpenAI
import json

if len(os.environ.get("GROQ_API_KEY")) > 30:
    from groq import Groq
    model = "mixtral-8x7b-32768"
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )
else:
    OPENAI_API_KEY = os.getenv('OPENAI_KEY')
    model = "gpt-4o"
    client = OpenAI(api_key=OPENAI_API_KEY)

def generate_script_from_article(article_content):
    # Step 1: Summarize the article content
    summarize_prompt = (
        """You are a skilled content summarizer. Your task is to summarize the following article in a concise and clear way, 
        capturing the main points and important details. The summary should be brief, with no more than 100 words.

        Article:
        {article_content}

        Please provide the summary of the article below:
        """
    ).format(article_content=article_content)

    # Summarize the article
    summarize_response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": summarize_prompt},
            {"role": "user", "content": article_content}
        ]
    )
    summary = summarize_response.choices[0].message.content.strip()

    # Step 2: Generate a script for a YouTube Shorts video based on the summary
    script_prompt = (
        """You are a creative YouTube Shorts scriptwriter. Based on the following summary, generate a concise, 
        engaging, and interesting script for a YouTube video that lasts about 30-40 seconds (approximately 87-100 words).

        Summary:
        {summary}

        The video script should be catchy, informative, and brief. Please format the output as a JSON object with the key 'script'.
        """
    ).format(summary=summary)

    # Generate the video script
    script_response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": script_prompt},
            {"role": "user", "content": summary}
        ]
    )
    
    content = script_response.choices[0].message.content
    try:
        script = json.loads(content)["script"]
    except Exception as e:
        # Clean up response if necessary and re-parse
        json_start_index = content.find('{')
        json_end_index = content.rfind('}')
        content = content[json_start_index:json_end_index+1]
        script = json.loads(content)["script"]
    
    return script
