from flask import Flask, redirect, url_for, request, session, render_template, jsonify
import requests
import threading
import cv2
import os
import gdown
import random
import time
from ultralytics import YOLO
from urllib.parse import urlencode
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


# MBTI Results
mbti_results = {
    "INTJ": "The Architect",
    "INFP": "The Mediator",
    "ENTJ": "The Commander",
    "ENFP": "The Campaigner",
    "ISTJ": "The Logistician",
    "ISFJ": "The Defender",
    "ESTJ": "The Executive",
    "ESFJ": "The Consul",
    "INTP": "The Logician",
    "INFJ": "The Advocate",
    "ENTP": "The Debater",
    "ENFJ": "The Protagonist",
    "ISFP": "The Adventurer",
    "ISTP": "The Virtuoso",
    "ESTP": "The Entrepreneur",
    "ESFP": "The Entertainer"
}




# Emotion-to-genre mapping with MBTI pairings
emotion_to_search_term = {
    "anger": {
        "ESTJ": "explosive hip-hop, energetic beats, hardcore, energetic korean pop, aggressive Korean rap, hardcore Japanese hip-hop",
        "ENTJ": "rock, metal, energetic, adrenaline, US rock, Japanese rock, Korean rock, unrelenting metal, intense Korean metal, brutal Japanese rock",
        "ESFJ": "upbeat pop, energetic, upbeat Filipino pop, powerful Korean pop, intense Japanese dance pop",
        "ENFJ": "rock, energetic pop, RnB, K-pop, explosive Filipino RnB, emotional Korean rock, dramatic Japanese RnB",
        "ISTJ": "classic rock, oldies, hard rock, explosive US oldies, explosive Korean oldies, explosive Japanese oldies, intense Korean rock, fiery Japanese classic rock",
        "ISFJ": "explosive classical, intense instrumental, distorted orchestral, dramatic Korean orchestral, aggressive Japanese symphonic rock",
        "INTJ": "adrenaline rock, metal, intense beats, US metal, chaotic Korean industrial metal, dark Japanese progressive metal",
        "INFJ": "grunge, unrelenting rock, aggressive Korean indie, aggressive Japanese indie, melancholic Korean post-rock, intense Japanese alternative",
        "ESTP": "heavy metal, aggressive hip-hop, energetic, aggressive K-pop, hardcore Korean trap, violent Japanese rap",
        "ESFP": "heavy pop punk, energetic dance, heavy rock, fast-paced Korean punk pop, rebellious Japanese dance rock",
        "ENTP": "punk rock, aggressive energetic indie, aggressive Korean punk, aggressive Japanese punk, chaotic Korean underground rock, wild Japanese punk fusion",
        "ENFP": "hard rock, gritty indie rock, aggressive beats, aggressive Filipino indie, explosive Korean garage rock, distorted Japanese alternative",
        "ISTP": "heavy punk rock, unrelenting beats, distorted Japanese punk, raw Korean hardcore punk, aggressive Japanese thrash punk",
        "ISFP": "aggressive punk, distorted pop, explosive Korean pop, rebellious Korean alt-pop, harsh Japanese electro-punk",
        "INTP": "heavy rock, heavy metal, alternative, heavy US alternative, extreme Korean alternative rock, dystopian Japanese noise rock",
        "INFP": "heavy alternative rock, unrelenting energetic indie, aggressive Korean rock, aggressive Japanese rock, emotional Korean emo rock, distorted Japanese dream punk"
    },
    "fear": {
        "ESTJ": "dark ambient, industrial, eerie beats, K-pop with suspenseful undertones, Korean horror synth, Japanese horror synth",
        "ENTJ": "synthwave, dark electronic, dystopian, Japanese industrial, Korean cyberpunk, aggressive Japanese horror synth",
        "ESFJ": "ambient, unsettling instrumental, Filipino eerie instrumental, haunting Korean ballads, eerie Japanese lullabies",
        "ENFJ": "ambient, haunting, suspenseful ballads, Korean dark ballads, cinematic horror scores, eerie Japanese folk",
        "ISTJ": "classic dark rock, unsettling instrumental, US horror rock, ominous Korean retro rock, suspenseful Japanese noir rock",
        "ISFJ": "orchestral, haunting classical, Japanese dark orchestral, unsettling Korean symphonic, eerie Western opera",
        "INTJ": "dark ambient, lo-fi with horror elements, US lo-fi dark beats, eerie Korean electronic, unsettling Japanese glitch music",
        "INFJ": "ambient, atmospheric tension, Filipino eerie ambient, deep Korean horror soundscapes, Japanese supernatural folk music",
        "ESTP": "heavy industrial, experimental electronic, Japanese suspense beats, dark Korean cyber-metal, eerie rhythmic percussion",
        "ESFP": "dark pop, eerie instrumental, Korean pop with tense melodies, experimental horror synth, ghostly Japanese dream pop",
        "ENTP": "ethereal, unsettling electronic, Japanese darkwave, chaotic Korean experimental, dystopian Japanese noise pop",
        "ENFP": "ambient, unsettling lo-fi, US experimental with dark tones, eerie Korean indie, haunting Japanese dreamwave",
        "ISTP": "dark electronic, minimalistic beats, Filipino industrial, creepy Korean trap, ominous Japanese trip-hop",
        "ISFP": "ethereal, haunting instrumental, K-pop with suspenseful vibes, ghostly Korean ballads, chilling Japanese neo-folk",
        "INTP": "lo-fi with eerie undertones, Japanese ambient, dark lo-fi, abstract Korean horror beats, unsettling Japanese music",
        "INFP": "dark instrumental, scary instrumental, dark acoustic, melancholic Korean post-rock, horror-inspired Japanese acoustic"
    },
    "happy": {
        "ESTJ": "upbeat pop, energetic, US pop, high-energy K-pop, feel-good Korean pop, cheerful Japanese pop",
        "ENTJ": "uplifting rock, high-energy metal, Japanese high-energy rock, positive US rock, energizing Korean rock",
        "ESFJ": "energizing pop, upbeat dance, feel-good, Filipino dance pop, joyful Korean dance pop, positive Japanese electro-pop",
        "ENFJ": "joyful RnB, energizing pop, energizing Korean pop, energizing US RnB, cheerful Filipino pop, vibrant Japanese pop",
        "ISTJ": "uplifting classic rock, joyful upbeat oldies, cheerful US classic rock, lively Japanese rock, classic upbeat Korean rock",
        "ISFJ": "uplifting pop, joyful acoustic, uplifting Filipino acoustic, gentle Korean acoustic, uplifting Japanese acoustic",
        "INTJ": "energizing indie rock, upbeat beats, Japanese indie rock, energizing Korean indie, positive US indie rock",
        "INFJ": "energizing indie pop, feel-good indie, Korean indie, uplifting Japanese indie, cheerful Filipino indie",
        "ESTP": "energizing pop, energetic dance, energizing beats, energetic Filipino dance, energetic Korean dance, joyful Japanese pop",
        "ESFP": "joyful dance pop, joyful upbeat music, fun US dance pop, fun Korean pop, vibrant Filipino pop",
        "ENTP": "fun indie pop, energizing alternative rock, energizing Korean alternative, upbeat Japanese alternative, feel-good US indie",
        "ENFP": "joyful funk, fun hip-hop, upbeat indie, joyful Filipino funk, energetic Korean pop, happy-go-lucky Japanese pop",
        "ISTP": "energizing electronic, upbeat synth, Japanese electronic, lively Korean synth pop, happy Japanese electro",
        "ISFP": "energizing indie acoustic, upbeat pop, fun US indie, joyful Filipino acoustic, cheerful K-pop",
        "INTP": "energizing indie, fun alt-pop, chill beats, fun Filipino alt-pop, uplifting Korean indie, sunny Japanese alt-pop",
        "INFP": "fun indie K-pop, happy Korean acoustic, energizing Japanese pop, uplifting Filipino pop, uplifting Japanese indie"
    },
    "sad": {
        "ESTJ": "sorrowful instrumental, melancholic mellow jazz, grieving US jazz, sorrowful Korean jazz, melancholic Japanese jazz",
        "ENTJ": "tragic ambient, desolate slow rock, Japanese melancholic ambient rock, sorrowful Korean rock",
        "ESFJ": "heartbroken ballads, slow jazz, acoustic Filipino ballads with longing, melancholic Korean ballads, sorrowful Japanese ballads",
        "ENFJ": "soulful blues, grieving, melancholic Korean soul, sorrowful Japanese soul",
        "ISTJ": "classic rock, slow aching ballads, US tragic slow ballads, sorrowful Japanese classic rock, grieving Korean classic rock, Japanese slow ballads, Korean slow ballads",
        "ISFJ": "sombre classical, heartbreaking instrumental, Japanese sorrowful classical, Korean emotional orchestral",
        "INTJ": "ambient, sorrowful slow metal, desolate US slow metal, Japanese melancholic metal, sorrowful Korean metal",
        "INFJ": "sad indie, melancholic alternative, Korean emotional indie with yearning, sorrowful Japanese indie",
        "ESTP": "soft rock, melancholic chill beats, Japanese sorrowful soft rock, grieving Korean soft rock",
        "ESFP": "acoustic, heartbreaking soft RnB, Filipino acoustic with grief, melancholic Korean acoustic, Japanese sorrowful RnB",
        "ENTP": "sorrowful indie, US melancholic lo-fi, Korean lo-fi, Japanese melancholic indie",
        "ENFP": "soft jazz, wistful lo-fi, Filipino melancholic jazz, sorrowful Korean jazz, Japanese jazzy melancholy",
        "ISTP": "sorrowful soft rock, chill desolate instrumental, Japanese sorrowful instrumental, Korean melancholic instrumental",
        "ISFP": "sorrowful blues, melancholic ambient acoustic, Filipino blues with longing, Japanese sorrowful blues, Korean melancholic blues",
        "INTP": "tragic rock, sorrowful melancholic beats, US sad rock, Japanese sad rock, Korean melancholic rock",
        "INFP": "heartbroken indie, acoustic, sorrowful Filipino indie, K-pop grieving ballads, Japanese melancholic indie, Korean sorrowful ballads"
    },
    "surprise": {
        "ESTJ": "upbeat pop with unexpected rhythms, US experimental pop, surprising K-pop with shifting tempos, Japanese pop with sudden energy bursts",
        "ENTJ": "electronic with chaotic surprise rhythms, Japanese glitch with unexpected soundscapes, thrilling experimental beats",
        "ESFJ": "feel-good pop with unexpected surprises, Filipino pop with tempo shifts and sudden bursts, Korean pop with joyful twists",
        "ENFJ": "RnB with shocking drops, K-pop with surprising tempo changes, unexpected mood swings in Korean pop",
        "ISTJ": "classic rock with surprising rhythmic shifts, US experimental classic rock, unexpected tempo changes in Japanese classic rock",
        "ISFJ": "soft classical with sudden orchestral surprises, Japanese classical with unexpected shifts in mood and tone",
        "INTJ": "experimental with unpredictable electronic beats, US glitch and IDM with surprising sound transitions",
        "INFJ": "indie experimental with sudden mood changes, Filipino avant-garde with unexpected transitions",
        "ESTP": "hip-hop with surprise beat changes, K-pop trap with unpredictable rhythms, Korean rap with surprising twists",
        "ESFP": "dance music with unexpected rhythms and tempo, Filipino EDM with shocking drops, Korean electronic with unexpected builds",
        "ENTP": "punk with surprise twists, Japanese experimental punk with unpredictable beats, indie punk with shocking changes",
        "ENFP": "indie with unexpected jazz melodies, Korean jazz fusion with surprising transitions, unexpected jazz shifts in US indie",
        "ISTP": "electronic synth with abrupt beat changes, US synthwave with surprise tempo shifts, Japanese synth with sudden beats",
        "ISFP": "ambient with unexpected melodies, Japanese post-rock with surprising musical builds, Filipino ambient with sudden changes",
        "INTP": "electronic experimental beats with sudden changes, US IDM with unexpected rhythm shifts, Japanese IDM with surprising moments",
        "INFP": "experimental indie with unpredictable melodies, Filipino indie with twists, Korean indie with unexpected mood changes"
    },
    "neutral": {
        "ESTJ": "instrumental pop, chill, US instrumental pop, mellow K-pop instrumental, relaxed Japanese instrumental",
        "ENTJ": "classical with instrumental beats, Japanese instrumental with a calming atmosphere, relaxed orchestral vibes",
        "ESFJ": "easy listening pop, acoustic, Filipino easy listening, peaceful K-pop, soothing Japanese instrumental",
        "ENFJ": "ambient pop with instrumental influences, Korean pop with a calm feel, neutral instrumental ballads",
        "ISTJ": "classic rock with mellow tones, oldies, US oldies with a steady beat, classic Japanese rock with a neutral vibe",
        "ISFJ": "soft classical, easy listening, Japanese soft classical with tranquil melodies, peaceful instrumental",
        "INTJ": "chill instrumental, ambient, US chill instrumental with subtle tones, soothing Japanese ambient",
        "INFJ": "indie acoustic, mellow, Filipino acoustic with calming guitar, peaceful K-pop indie",
        "ESTP": "chill beats, pop with a relaxed vibe, Filipino chill beats with a laid-back tempo, smooth Korean beats",
        "ESFP": "ambient, dance beats with a mellow feel, Korean dance with a relaxed tone, Filipino chill dance beats",
        "ENTP": "indie with chill rock elements, Japanese chill rock with a soft beat, relaxed indie rock",
        "ENFP": "indie pop, ambient, Filipino pop with a calm atmosphere, relaxed Korean pop with mellow vibes",
        "ISTP": "instrumental electronic with subtle beats, Japanese electronic with a chill tone, smooth instrumental",
        "ISFP": "chill ambient, indie, Filipino ambient with a soothing feel, Japanese ambient with relaxed melodies",
        "INTP": "ambient instrumental rock with a mellow flow, US instrumental with neutral beats, Japanese instrumental with calm ambiance",
        "INFP": "indie folk with a mellow atmosphere, Filipino folk with soothing melodies, Korean indie with a neutral vibe"
    },
}


# Spotify API credentials
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

# Spotify URLs
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"




# Path to the YOLO model in your GitHub repository
MODEL_PATH = "Yolo-Weights/best.pt"

# Check if the model exists
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file '{MODEL_PATH}' not found. Make sure it's in your GitHub repository.")

# Load the YOLO model
model = YOLO(MODEL_PATH)
classNames = ["anger", "fear", "happy", "neutral", "sad", "surprise"]


# Global variables
detected_emotion = None
emotion_songs = []
current_song_index = 0
is_paused = False



@app.route('/user')
def user():
    return render_template('User Manual.html')



# Personality types HTML ROUTING
# PURPLE
@app.route('/intj')
def intj():
    return render_template('intj.html')

@app.route('/intp')
def intp():
    return render_template('intp.html')

@app.route('/entj')
def entj():
    return render_template('entj.html')

@app.route('/entp')
def entp():
    return render_template('entp.html')

# GREEN
@app.route('/infj')
def infj():
    return render_template('infj.html')

@app.route('/infp')
def infp():
    return render_template('infp.html')

@app.route('/enfj')
def enfj():
    return render_template('enfj.html')

@app.route('/enfp')
def enfp():
    return render_template('enfp.html')

# BLUE
@app.route('/istj')
def istj():
    return render_template('istj.html')

@app.route('/isfj')
def isfj():
    return render_template('isfj.html')

@app.route('/estj')
def estj():
    return render_template('estj.html')

@app.route('/esfj')
def esfj():
    return render_template('esfj.html')

# YELLOW
@app.route('/istp')
def istp():
    return render_template('istp.html')

@app.route('/isfp')
def isfp():
    return render_template('isfp.html')

@app.route('/estp')
def estp():
    return render_template('estp.html')

@app.route('/esfp')
def esfp():
    return render_template('esfp.html')






# Home, Quiz, Result Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/result')
def result():

    personality_type = request.args.get('personality_type', '')
    description = mbti_results.get(personality_type, "Unknown type")

    session.permanent = True  # Keep session persistent

    # Store MBTI type in session
    session['personality_type'] = personality_type  # Store in session
    session['description'] = description  # Store in session

    print("Stored in session:", session.get('personality_type'), session.get('description'))  # Debugging

    return render_template('result.html', personality_type=personality_type, description=description)


# Emotion detection function
def run_emotion_detection_on_image(image_path, access_token, personality_type):
    global detected_emotion, emotion_songs  # Ensure we are using the global variable

    # Load the uploaded image
    img = cv2.imread(image_path)
    results = model(img, stream=True)

    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            detected_emotion = classNames[cls]

            # Fetch songs for the detected emotion
            fetched_songs = fetch_songs_for_emotion(detected_emotion, personality_type, access_token)

            if fetched_songs:
                emotion_songs = fetched_songs  # Update the global emotion_songs list
                current_song_index = 0  # Start playing from the first song in the list
                play_song(emotion_songs[current_song_index], access_token)  # Play the first song
                return  # Once the first song is played, exit the loop

    print("No emotions detected or no songs returned.")





# Image upload route
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'access_token' not in session:
        return redirect(url_for('login_spotify'))

    access_token = session['access_token']

    # Get the uploaded file
    file = request.files['image']
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)

        # Extract personality type before starting the thread
        personality_type = session.get('personality_type', 'Not Available')
        # Run emotion detection on the uploaded image
        threading.Thread(target=run_emotion_detection_on_image, args=(file_path, access_token, personality_type)).start()

        # Return to the Spotify page (can update the UI with detected emotion later)
        return redirect(url_for('spotify'))

    return "Error: No file uploaded."


# Fetch songs based on emotion
def fetch_songs_for_emotion(emotion, personality_type, access_token):
    headers = {'Authorization': f"Bearer {access_token}"}

    # Fallback to "chill vibes" if emotion is not mapped
    search_terms = emotion_to_search_term.get(emotion, {}).get(personality_type, "chill vibes")

    print(f"Fetching songs for emotion '{emotion}' and MBTI '{personality_type}': {search_terms}")  # Debugging

    # Define search parameters
    params = {
        'q': search_terms,  # Use a comma-separated list of terms for broader results
        'type': 'track',
        'limit': 50,  # MAX LIMIT FOR SPOTIFY API
        'market': 'US, PH, JP,KR'  # Include the markets (US, Philippines, Japan, Korea)
    }

    # Perform the search
    response = requests.get(f"{SPOTIFY_API_BASE_URL}/search", headers=headers, params=params)

    if response.status_code == 200:
        tracks = response.json().get('tracks', {}).get('items', [])
        print(f"Found {len(tracks)} tracks for search terms: {search_terms}")  # Debugging
        if not tracks:
            print(f"No results found for search terms: {search_terms}")
            return []

        # Sort tracks by popularity (highest first)
        sorted_tracks = sorted(tracks, key=lambda x: x['popularity'], reverse=True)

        # Select top 3 popular tracks
        top_tracks = sorted_tracks[:3]

        # The remaining tracks will be chosen randomly from the rest
        remaining_tracks = sorted_tracks[3:]
        random.shuffle(remaining_tracks)

        # This will give you a mix of the top 3 most popular tracks based on your search terms
        # and 3 random songs selected from the rest of the search results.

        # Combine top tracks and random tracks
        final_tracks = top_tracks + remaining_tracks

        # Extract essential track details
        return [
            {
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'cover_url': track['album']['images'][0]['url'] if track['album']['images'] else '',
                'popularity': track['popularity']
            }
            for track in final_tracks
        ]
    else:
        print(f"Error fetching songs for {emotion}: {response.status_code} - {response.text}")
        return []



# Function to play a song on the active device
def play_song(song, access_token):
    headers = {
        'Authorization': f"Bearer {access_token}"
    }

    # Get available devices
    devices_response = requests.get(f"{SPOTIFY_API_BASE_URL}/me/player/devices", headers=headers)
    devices = devices_response.json().get('devices', [])
    if not devices:
        print("No active devices found.")
        return

    device_id = devices[0]['id']  # Use the first available device
    track_uri = f"spotify:track:{song['id']}"
    play_url = f"{SPOTIFY_API_BASE_URL}/me/player/play?device_id={device_id}"

    # Activate the device
    activate_device_response = requests.put(
        f"{SPOTIFY_API_BASE_URL}/me/player",
        headers=headers,
        json={"device_ids": [device_id]}
    )
    print(f"Activate device response: {activate_device_response.status_code}")  # Debugging

    # Start playback
    start_playback_response = requests.put(play_url, headers=headers, json={"uris": [track_uri]})
    if start_playback_response.status_code == 204:
        print(f"Playing: {song['name']} by {song['artist']} with {song['popularity']} popularity on device {devices[0]['name']}")
    else:
        print(f"Failed to play song: {start_playback_response.text}")

# Spotify login route
@app.route('/login_spotify')
def login_spotify():
    if 'access_token' in session:
        return redirect(url_for('spotify'))

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': 'user-read-playback-state user-modify-playback-state user-read-private user-read-email streaming',
    }
    url = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    return redirect(url)

# Spotify OAuth callback
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        response = requests.post(SPOTIFY_TOKEN_URL, data=data)
        token_info = response.json()

        if 'access_token' in token_info:
            session['access_token'] = token_info['access_token']
            session['refresh_token'] = token_info.get('refresh_token')
            return redirect(url_for('spotify'))
    return "Error: Authorization failed."

# Spotify home route
@app.route('/spotify')
def spotify():
    if 'access_token' not in session:
        return redirect(url_for('login_spotify'))

    print("Retrieving from session:", session.get('personality_type'), session.get('description'))  # Debugging

    personality_type = session.get('personality_type', 'Not Available')
    description = session.get('description', 'No description available')

    return render_template('spotify.html', access_token=session['access_token'], personality_type=personality_type,
                           description=description)

@app.route('/reset_spotify')
def reset_spotify():
    session.pop('access_token', None)  # Remove access token from session
    session.pop('refresh_token', None)  # Remove refresh token as well (if exists)

    return redirect(url_for('login_spotify'))  # Redirect to Spotify login


# Start emotion detection
@app.route('/detect_emotion')
def detect_emotion():
    if 'access_token' not in session:
        return redirect(url_for('login_spotify'))

    access_token = session['access_token']
    threading.Thread(target=run_emotion_detection_on_image, args=(access_token,)).start()
    return redirect(url_for('spotify'))

# Control song playback
@app.route('/control/<action>')
def control(action):
    global current_song_index, is_paused

    if not emotion_songs:
        return jsonify({'error': 'No songs available to control'})

    access_token = session.get('access_token')
    if not access_token:
        return jsonify({'error': 'Access token is missing'})

    headers = {'Authorization': f'Bearer {access_token}'}

    if action == 'playpause':
        if is_paused:
            requests.put(f"{SPOTIFY_API_BASE_URL}/me/player/play", headers=headers)
            is_paused = False
        else:
            requests.put(f"{SPOTIFY_API_BASE_URL}/me/player/pause", headers=headers)
            is_paused = True
    elif action == 'next':
        current_song_index = (current_song_index + 1) % len(emotion_songs)
        play_song(emotion_songs[current_song_index], access_token)
    elif action == 'previous':
        current_song_index = (current_song_index - 1) % len(emotion_songs)
        play_song(emotion_songs[current_song_index], access_token)

    song = emotion_songs[current_song_index]
    return jsonify({
        'song': {
            'name': song['name'],
            'artist': song['artist'],
            'album': song['album'],
            'cover_url': song.get('cover_url', '')
        },
        'is_paused': is_paused
    })

@app.route('/get_detected_emotion')
def get_detected_emotion():
    return jsonify({'detected_emotion': detected_emotion})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))  # Default to port 8080 if PORT is not set
    app.run(debug=False, host='0.0.0.0', port=port)



