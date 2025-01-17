import argparse
import asyncio
import requests
from bs4 import BeautifulSoup
from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.render.render_engine import render_video
from utility.video.video_search_query_generator import generate_video_url, merge_empty_intervals

def scrape_article_content(article_url):
    try:
        response = requests.get(article_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        article_content = " ".join([p.get_text(strip=True) for p in paragraphs])

        if not article_content:
            raise ValueError("No content found in the article.")

        return article_content
    except Exception as e:
        raise Exception(f"Error scraping article content: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video from an article URL.")
    parser.add_argument("url", type=str, help="The URL of the article to convert into a video")
    parser.add_argument("--output", type=str, default="output_video.mp4", help="The name of the output video file")

    args = parser.parse_args()
    ARTICLE_URL = args.url
    OUTPUT_FILE_NAME = args.output
    AUDIO_FILE_NAME = "audio_tts.wav"
    VIDEO_SERVER = "pexel"

    try:
        article_content = scrape_article_content(ARTICLE_URL)
        print(f"Scraped Article Content: {article_content[:500]}...")
    except Exception as e:
        print(f"Error scraping article content: {e}")
        exit(1)

    try:
        script = generate_script(article_content)
        print(f"Generated Script: {script}")
    except Exception as e:
        print(f"Error generating script: {e}")
        exit(1)

    try:
        asyncio.run(generate_audio(script, AUDIO_FILE_NAME))
        print(f"Audio file generated: {AUDIO_FILE_NAME}")
    except Exception as e:
        print(f"Error generating audio: {e}")
        exit(1)

    try:
        timed_captions = generate_timed_captions(AUDIO_FILE_NAME)
        print(f"Timed Captions: {timed_captions}")
    except Exception as e:
        print(f"Error generating timed captions: {e}")
        exit(1)

    try:
        search_terms = generate_video_url(script, timed_captions)
        print(f"Search Terms for Videos: {search_terms}")
    except Exception as e:
        print(f"Error generating search terms: {e}")
        search_terms = None

    try:
        background_video_urls = merge_empty_intervals(search_terms)
        if background_video_urls:
            print(f"Background Video URLs: {background_video_urls}")
        else:
            print("No background video URLs found.")
    except Exception as e:
        print(f"Error merging empty intervals: {e}")
        background_video_urls = None

    try:
        if background_video_urls:
            render_video(AUDIO_FILE_NAME, timed_captions, background_video_urls, OUTPUT_FILE_NAME, VIDEO_SERVER)
            print(f"Video successfully created: {OUTPUT_FILE_NAME}")
        else:
            print("No video rendered due to missing background videos.")
    except Exception as e:
        print(f"Error rendering video: {e}")
