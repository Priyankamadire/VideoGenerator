import spacy
from spacy.lang.en.stop_words import STOP_WORDS

# Step 1: Enhanced Keyword Extraction with Stopword Removal
def extract_keywords_from_script(script):
    """
    Extract visually concrete keywords from the summarized script using NLP,
    excluding common stopwords.
    
    :param script: Summarized script
    :return: List of keywords
    """
    # Process the script with spaCy
    doc = nlp(script)
    
    # Initialize the list of keywords
    keywords = []
    
    # Extract nouns, adjectives, and verbs (POS tagging) while removing stop words
    for sentence in script.split("."):
        if len(sentence.split()) > 3:  # Only consider sentences with more than 3 words
            for token in nlp(sentence):  # Process each sentence separately
                if token.pos_ in ["NOUN", "ADJ", "VERB"] and token.text.lower() not in STOP_WORDS:
                    keywords.append(token.text)
    
    # Optionally, add Named Entity Recognition (NER) results
    for ent in doc.ents:
        if ent.text.lower() not in STOP_WORDS:  # Exclude NER stop words
            keywords.append(ent.text)
    
    return list(set(keywords))  # Return unique keywords

# Step 2: Enhanced Video Search with Pagination
def search_videos(query_string, orientation_landscape=True, page=1):
    """
    Search for videos using the Pexels API with pagination support.
    
    :param query_string: The search term for finding videos
    :param orientation_landscape: Boolean flag to specify landscape (True) or portrait (False) orientation
    :param page: Pagination page number
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
        "per_page": 15,
        "page": page
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

# Step 3: Modify Video Selection with Error Handling and Pagination
def getBestVideo(query_string, orientation_landscape=True, used_vids=[], max_pages=3):
    """
    Get the best video link from the Pexels API based on search query and orientation,
    with pagination and improved error handling.
    
    :param query_string: The search term for finding videos
    :param orientation_landscape: Boolean flag to specify landscape (True) or portrait (False) orientation
    :param used_vids: List of previously used video links to avoid reuse
    :param max_pages: Maximum number of pages to search through
    :return: URL of the best video or None if no valid video found
    """
    vids = []
    for page in range(1, max_pages + 1):  # Loop through pages
        result = search_videos(query_string, orientation_landscape, page)
        if 'videos' not in result:
            continue  # Skip this page if no videos are found
        
        videos = result['videos']  # Extract the videos list from JSON
        # Filter and extract videos based on dimensions
        if orientation_landscape:
            filtered_videos = [video for video in videos if video['width'] >= 1920 and video['height'] >= 1080 and video['width'] / video['height'] == 16 / 9]
        else:
            filtered_videos = [video for video in videos if video['width'] >= 1080 and video['height'] >= 1920 and video['height'] / video['width'] == 16 / 9]

        # Sort videos by duration in ascending order (closest to 15 seconds)
        sorted_videos = sorted(filtered_videos, key=lambda x: abs(15 - int(x['duration'])))

        for video in sorted_videos:
            for video_file in video['video_files']:
                if (orientation_landscape and video_file['width'] == 1920 and video_file['height'] == 1080) or \
                   (not orientation_landscape and video_file['width'] == 1080 and video_file['height'] == 1920):
                    if video_file['link'].split('.hd')[0] not in used_vids:
                        used_vids.append(video_file['link'].split('.hd')[0])
                        return video_file['link']
    
    print(f"No valid video found for query: {query_string}")
    return None
