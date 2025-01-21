import os
import requests
from openai import OpenAI
from utility.utils import log_response, LOG_TYPE_PEXEL

# Fetch the Pexels API Key from environment variables
PEXELS_API_KEY = os.environ.get('PEXELS_KEY')

# OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_KEY')  # Fetch OpenAI API key from environment variables

def extract_keywords_from_script(script):
    """
    Extract visually concrete keywords from the summarized script using a language model.
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
        
        # Ensure keywords are returned and not empty
        if not keywords:
            raise ValueError("No keywords extracted.")
        
        # Split and clean keywords
        keywords_list = [keyword.strip() for keyword in keywords.split(',')]
        return keywords_list
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return []

def search_videos(query_string, orientation_landscape=True):
    """
    Search for videos using the Pexels API.
    """
    if not query_string:
        print("No valid search terms provided.")
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

        # Validate JSON structure
        if not isinstance(json_data, dict) or 'videos' not in json_data:
            raise ValueError("Invalid JSON structure: 'videos' key missing.")

        log_response(LOG_TYPE_PEXEL, query_string, json_data)  # Optional: Log the response
        return json_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching videos: {e}")
        return {}

def get_best_video(query_string, orientation_landscape=True, used_vids=[]):
    """
    Get the best video URL from the Pexels API based on search query and orientation.
    """
    if not query_string:
        print(f"Skipping video search for empty query string.")
        return None  # Skip if no valid search term

    videos_data = search_videos(query_string, orientation_landscape)
    if 'videos' not in videos_data:
        print(f"No videos found for query: {query_string}")
        return None  # Return None if 'videos' key doesn't exist in the response

    videos = videos_data['videos']

    # Filter videos by resolution and aspect ratio
    filtered_videos = [
        video for video in videos if
        (video.get('width') / video.get('height') == (16 / 9) if orientation_landscape else (9 / 16))
    ]

    # Sort videos by duration closest to 15 seconds
    sorted_videos = sorted(filtered_videos, key=lambda x: abs(15 - int(x.get('duration', 0))))

    # Select the best video that hasn't been used
    for video in sorted_videos:
        for video_file in video.get('video_files', []):
            if video_file.get('link') not in used_vids:
                used_vids.append(video_file.get('link'))
                return video_file.get('link')

    return None

def generate_video_url(timed_video_searches, video_server="pexel"):
    """
    Generate video URLs for each segment based on timed video searches.
    """
    timed_video_urls = []

    if video_server == "pexel":
        used_links = []
        for (t1, t2), search_terms in timed_video_searches:
            if not search_terms:
                print(f"Skipping empty search terms for interval ({t1}, {t2})")
                continue  # Skip if search terms are empty

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
    """
    try:
        # Step 1: Extract keywords
        keywords = extract_keywords_from_script(script)

        # Check if keywords are empty
        if not keywords:
            print("No keywords extracted, skipping video generation.")
            return []

        # Step 2: Generate timed video searches
        timed_video_searches = [[(0, 15), [keyword]] for keyword in keywords]

        # Step 3: Generate video URLs using the video server
        timed_video_urls = generate_video_url(timed_video_searches, video_server="pexel")

        # Check if no valid video URLs were found
        if not timed_video_urls:
            print("No background video found.")
            return []

        return timed_video_urls
    except Exception as e:
        print(f"Error generating video from article: {e}")
        return []
