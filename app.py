import sys
import requests
import asyncio
from bs4 import BeautifulSoup
from utility.script.script_generator import generate_script_from_article
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.render.render_engine import get_output_media
from utility.video.background_video_generator import generate_video_url
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals

def fetch_article_content(url):
    """
    Fetches article content from a given URL and parses it using BeautifulSoup.
    
    :param url: The URL of the article.
    :return: Tuple containing the title and article content.
    """
    try:
        # Fetch article content using requests
        response = requests.get(url)
        response.raise_for_status()  # Will raise an error for 4xx/5xx status codes
        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title and body content (adjust depending on structure)
        title = soup.title.string if soup.title else "No title"
        paragraphs = soup.find_all('p')
        article_content = "\n".join([para.get_text() for para in paragraphs])
        
        return title, article_content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching article: {e}")
        return None, None

async def generate_video_from_article(url):
    """
    Generates a video from an article by extracting content, generating script, audio, captions, 
    and background video based on the script.
    
    :param url: The URL of the article.
    """
    # Fetch and parse article content
    title, article_content = fetch_article_content(url)
    if not article_content:
        print("Failed to fetch or parse article.")
        return
    
    print(f"Processing article: {title}")
    
    # Generate script from article content
    script = generate_script_from_article(article_content)
    print("Generated Script: ", script)
    
    # Generate audio from script
    audio_filename = "audio_output.mp3"
    await generate_audio(script, audio_filename)

    # Generate timed captions from audio file
    timed_captions = generate_timed_captions(audio_filename)
    
    # Generate video search queries based on script and timed captions
    search_terms = getVideoSearchQueriesTimed(script, timed_captions)
    print("Search Terms: ", search_terms)

    # Generate background video URLs based on the search terms
    background_video_urls = None
    if search_terms:
        background_video_urls = generate_video_url(search_terms, "pexel")
        print("Background Video URLs: ", background_video_urls)
    else:
        print("No background video found.")

    # Merge empty intervals if needed (this may be optional depending on your use case)
    if background_video_urls:
        background_video_urls = merge_empty_intervals(background_video_urls)
        print(f"Final Background Video URLs: {background_video_urls}")
    
    # Create the final video with audio, captions, and background video
    if background_video_urls:
        final_video = get_output_media(audio_filename, timed_captions, background_video_urls, video_server="pexel")
        print(f"Video generated and saved as {final_video}")
    else:
        print("No video generated due to lack of background video URLs.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the article URL.")
        sys.exit(1)
    
    # Get the article URL from command-line arguments
    url = sys.argv[1]
    
    # Run the async function with asyncio
    asyncio.run(generate_video_from_article(url))
