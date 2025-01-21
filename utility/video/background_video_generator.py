import os
import requests
import openai
from utility.utils import log_response, LOG_TYPE_PEXEL

# Fetch the Pexels API Key from environment variables
PEXELS_API_KEY = os.environ.get('PEXELS_KEY')

# OpenAI API Key
openai.api_key = os.getenv('OPENAI_KEY')  # Fetch OpenAI API key from environment variables

def extract_keywords_from_script(script):
    """
    Extract visually concrete keywords from the summarized script using a language model.

    :param script: Summarized script as a string
    :return: List of keywords
    """
    sentences = script.split(".")  # Tokenize the script into sentences
    
    # Prepare the prompt for extracting keywords
    prompt = "Extract visually concrete keywords from the following text:\n" + script + "\nKeywords:"
    
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # You can use GPT-4 if available
            prompt=prompt,
            max_tokens=100,
            temperature=0.5
        )
        keywords = response.choices[0].text.strip()
        if not keywords:
            raise ValueError("No keywords extracted.")
        
        keywords_list = keywords.split(',')
        return [keyword.strip() for keyword in keywords_list]  # Clean and return keywords
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return []

def search_videos(query_string, orientation_landscape=True):
    """
    Search for videos using the Pexels API.

    :param query_string: The search term for finding videos
    :param orientation_landscape: Boolean flag to specify landscape (True) or portrait (False) orientation
    :return: JSON response containing video data
    """
    if not query_string:
        print("No search terms provided.")
        return {}

    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    params = {
        "query": query_string,
        "orientation": "landscape" if orientation_landscape else "portrait",
        "per_page": 15
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for HTTP status codes != 200
        json_data = response.json()
        log_response(LOG_TYPE_PEXEL, query_string, json_data)  # Optional: Log the response
        return json_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching videos: {e}")
        return {}

def get_best_video(query_string, orientation_landscape=True, used_vids=[]):
    """
    Get the best video URL from the Pexels API based on search query and orientation.

    :param query_string: The search term for finding videos
    :param orientation_landscape: Boolean flag for landscape (True) or portrait (False) orientation
    :param used_vids: List of previously used video links to avoid reuse
    :return: URL of the best video or None if no valid video is found
    """
    videos_data = search_videos(query_string, orientation_landscape)
    if 'videos' not in videos_data:
        print("No videos found for query:", query_string)
        return None  # Return None if 'videos' key doesn't exist in the response

    videos = videos_data['videos']

    # Filter videos by resolution and aspect ratio
    filtered_videos = [
        video for video in videos if
        (video['width'] / video['height'] == (16 / 9) if orientation_landscape else (9 / 16))
    ]

    # Sort videos by duration closest to 15 seconds
    sorted_videos = sorted(filtered_videos, key=lambda x: abs(15 - int(x['duration'])))

    # Select the best video that hasn't been used
    for video in sorted_videos:
        for video_file in video['video_files']:
            if video_file['link'] not in used_vids:
                used_vids.append(video_file['link'])
                return video_file['link']

    return None

def generate_video_url(timed_video_searches, video_server="pexel"):
    """
    Generate video URLs for each segment based on timed video searches.

    :param timed_video_searches: List of tuples containing time intervals and search terms (keywords)
    :param video_server: The video server to use ('pexel' or 'stable_diffusion')
    :return: List of timed video URLs
    """
    timed_video_urls = []

    if video_server == "pexel":
        used_links = []
        for (t1, t2), search_terms in timed_video_searches:
            if not search_terms:
                print(f"Skipping empty search terms for interval ({t1}, {t2})")
                continue

            url = None
            for query in search_terms:
                url = get_best_video(query, orientation_landscape=True, used_vids=used_links)
                if url:
                    break  # Stop once a valid video is found
            timed_video_urls.append([[t1, t2], url])

    elif video_server == "stable_diffusion":
        print("Stable Diffusion is not implemented in this code.")  # Placeholder for custom implementation

    return timed_video_urls

def generate_video_from_article(script):
    """
    Generate a video from the summarized script by searching for relevant background videos.

    :param script: The summarized script
    :return: List of timed video URLs
    """
    try:
        # Step 1: Extract keywords
        keywords = extract_keywords_from_script(script)

        if not keywords:
            print("No keywords extracted, skipping video generation.")
            return []

        # Step 2: Generate timed video searches
        timed_video_searches = [[(0, 15), [keyword]] for keyword in keywords]

        # Step 3: Generate video URLs using the video server
        timed_video_urls = generate_video_url(timed_video_searches, video_server="pexel")

        if not timed_video_urls:
            print("No background video found.")
            return []

        return timed_video_urls
    except Exception as e:
        print(f"Error generating video from article: {e}")
        return []
