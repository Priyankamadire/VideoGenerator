import os
import requests
from utility.utils import log_response, LOG_TYPE_PEXEL

PEXELS_API_KEY = os.environ.get('PEXELS_KEY')

# Step 1: Extracting Keywords from Summarized Script
def extract_keywords_from_script(script):  
    """
    Extract visually concrete keywords from the summarized script.
    
    :param script: Summarized script
    :return: List of keywords
    """
    # Simple logic to extract keywords (You can refine this with NLP libraries)
    keywords = []
    sentences = script.split(".")  # Split the script into sentences
    
    for sentence in sentences:
        # If sentence has more than 3 words, it's likely useful for video search
        if len(sentence.split()) > 3:
            keywords.append(sentence.strip())
    
    return keywords

# Step 2: Searching for Videos on Pexels API
def search_videos(query_string, orientation_landscape=True):
    """
    Search for videos using the Pexels API.
    
    :param query_string: The search term for finding videos
    :param orientation_landscape: Boolean flag to specify landscape (True) or portrait (False) orientation
    :return: JSON response containing video data
    """
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    params = {
        "query": query_string,
        "orientation": "landscape" if orientation_landscape else "portrait",
        "per_page": 15
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error if the status code is not 200
        json_data = response.json()
        log_response(LOG_TYPE_PEXEL, query_string, json_data)
        return json_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching videos: {e}")
        return {}

# Step 3: Get the Best Video based on Search Keywords
def getBestVideo(query_string, orientation_landscape=True, used_vids=[]):
    """
    Get the best video link from the Pexels API based on search query and orientation.
    
    :param query_string: The search term for finding videos
    :param orientation_landscape: Boolean flag to specify landscape (True) or portrait (False) orientation
    :param used_vids: List of previously used video links to avoid reuse
    :return: URL of the best video or None if no valid video found
    """
    vids = search_videos(query_string, orientation_landscape)
    if 'videos' not in vids:
        return None  # Ensure the 'videos' field exists
    
    videos = vids['videos']  # Extract the videos list from JSON

    # Filter and extract videos based on dimensions
    if orientation_landscape:
        filtered_videos = [video for video in videos if video['width'] >= 1920 and video['height'] >= 1080 and video['width'] / video['height'] == 16 / 9]
    else:
        filtered_videos = [video for video in videos if video['width'] >= 1080 and video['height'] >= 1920 and video['height'] / video['width'] == 16 / 9]

    # Sort videos by duration in ascending order (closest to 15 seconds)
    sorted_videos = sorted(filtered_videos, key=lambda x: abs(15 - int(x['duration'])))

    # Extract the top 3 videos' URLs
    for video in sorted_videos:
        for video_file in video['video_files']:
            if orientation_landscape and video_file['width'] == 1920 and video_file['height'] == 1080:
                if video_file['link'].split('.hd')[0] not in used_vids:
                    used_vids.append(video_file['link'].split('.hd')[0])
                    return video_file['link']
            elif not orientation_landscape and video_file['width'] == 1080 and video_file['height'] == 1920:
                if video_file['link'].split('.hd')[0] not in used_vids:
                    used_vids.append(video_file['link'].split('.hd')[0])
                    return video_file['link']
    
    print(f"No valid links found for query: {query_string}")
    return None

# Step 4: Generate Video URLs for the Given Script
def generate_video_url(timed_video_searches, video_server):
    """
    Generate video URLs for each segment of timed video searches based on keywords from summarized script.
    
    :param timed_video_searches: List of tuples containing time intervals and search terms (keywords)
    :param video_server: The video server to use ('pexel' or 'stable_diffusion')
    :return: List of timed video URLs
    """
    timed_video_urls = []

    if video_server == "pexel":
        used_links = []
        for (t1, t2), search_terms in timed_video_searches:
            url = None
            for query in search_terms:
                url = getBestVideo(query, orientation_landscape=True, used_vids=used_links)
                if url:
                    used_links.append(url.split('.hd')[0])  # Mark video as used
                    break  # Move to next time segment once we find a video
            timed_video_urls.append([[t1, t2], url])  # Append video URL for current segment
    
    elif video_server == "stable_diffusion":
        timed_video_urls = get_images_for_video(timed_video_searches)  # Assuming this is defined elsewhere

    return timed_video_urls

# Step 5: Generate Video from Article
def generate_video_from_article(script):
    """
    Generate a video from the summarized script by searching for relevant background videos.
    
    :param script: The summarized script
    :return: List of timed video URLs
    """
    try:
        # Extract keywords from the script
        keywords = extract_keywords_from_script(script)
        
        # Generate timed video search queries based on extracted keywords
        timed_video_searches = []
        for keyword in keywords:
            timed_video_searches.append([(0, 15), [keyword]])  # Assuming each keyword represents a 15-second segment
        
        # Generate video URLs from Pexels
        timed_video_urls = generate_video_url(timed_video_searches, video_server="pexel")

        return timed_video_urls

    except Exception as e:
        print(f"Error in generating video from article: {e}")
        return None
