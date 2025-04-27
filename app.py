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
    "ESTJ": "explosive filipino hip-hop, explosive japanese hip-hop, explosive korean hip-hop, explosive marching band, explosive filipino rock, explosive japanese rock, explosive korean rock",
    "ENTJ": "explosive jazz, aggressive rock, aggressive filipino rock, aggressive japanese rock, aggressive korean rock", #explosive filipino jazz, explosive japanese jazz, explosive korean jazz
    "ESFJ": "intense filipino pop, intense japanese pop, intense korean pop", #instense soul intense blue  intense filipino blues, intense japanese blues, intense korean blues
    "ENFJ": "angry loud filipino pop, angry loud korean pop, angry loud japanese pop",
    "ISTJ": "angry loud rock, angry loud japanese rock",
    "ISFJ": "aggressive classical", # religious fury angry filipino classical
    "INTJ": "aggressive korean metal, aggressive japanese metal, explosive metal, explosive rock, aggressive japanese rock",
    "INFJ": "intense alternative rock, turbulent world, intense japanese alternative rock, intense korean alternative rock",
    "ESTP": "intense japanese metal, intense korean rap, intense hip-hop, intense korean hip-hop, intense rap",
    "ESFP": "angry loud japanese hip-hop, intense korean hip-hop, intense loud hip-hop,",
    "ENTP": "aggressive alternative rock, angry punk, blazing japanese rock, blazing korean rock", #explosive filipino classical
    "ENFP": "aggressive heavy electronica, aggressive heavy hip-hop, aggressive heavy funk",
    "ISTP": "rebellious punk, rebellious filipino punk, rebellious japanese punk, rebellious korean punk",
    "ISFP": "aggressive heavy metal, aggressive heavy japanese metal", #not reggae
    "INTP": "angry punk, aggressive rock, explosive metal, angry filipino punk, angry japanese punk, angry korean punk, aggressive filipino rock, aggressive japanese rock, aggressive korean rock",
    "INFP": "aggressive heavy japanese punk, aggressive heavy korean punk, aggressive heavy japanese rock, aggressive heavy korean rock"
  },
  "fear": {
    "ESTJ": "horror synth",
    "ENTJ": "frightening classical, frightening japanese classical, frightening jazz, dark jazz, dark classical", #eerie filipino jazz, eerie japanese jazz, eerie korean jazz eerie jazz frightening korean classical frightening filipino classical frightening electronica
    "ESFJ": "horror blues, horror country, horror pop",
    "ENFJ": "horror blues, horror rnb, horror soul",
    "ISTJ": "horror synth", #not oldies or rock
    "ISFJ": "haunting classical", #religious filipino tranquility
    "INTJ": "haunting classical", # since adding other, like korean classic makes it recommend like ost
    "INFJ": "horror synth",     #not one of the genre
    "ESTP": "horror synth",
    "ESFP": "dark ambient, eerie ambient, dark japanese ambient",
    "ENTP": "gothic rock, japanese gothic rock",
    "ENFP": "darkwave electro",
    "ISTP": "haunting punk, haunting filipino punk, haunting japanese punk, haunting korean punk",
    "ISFP": "dark ambient, eerie ambient, dark japanese ambient, dark korean ambient despair",
    "INTP": "horror synth", # not rock metal punk
    "INFP": "haunting punk, haunting filipino punk, haunting japanese punk, haunting korean punkx"
  },
  "happy": {
    "ESTJ": "happy upbeat filipino hip-hop, happy upbeat japanese hip-hop, happy upbeat korean hip-hop, happy upbeat filipino rock, happy upbeat japanese rock, happy upbeat korean rock", #joyful patriotic, joyful marching band
    "ENTJ": "happy upbeat japanese jazz, happy upbeat korean jazz, happy upbeat japanese rock, happy upbeat korean rock", #happy upbeat electronica  happy upbeat filipino classical happy upbeat filipino jazz
    "ESFJ": "happy upbeat korean pop, happy upbeat japanese pop", #happy upbeat country happy upbeat blues
    "ENFJ": "happy upbeat korean pop, happy upbeat japanese pop, happy upbeat filipino pop, happy upbeat jazz, happy upbeat country",
    "ISTJ": "happy upbeat rock, happy upbeat korean rock, happy upbeat japanese rock",
    "ISFJ": "cheerful classical, cheerful classical, cheerful classical",
    "INTJ": "bright classical, bright japanese classical, bright japanese rock, bright korean rock",
    "INFJ": "joyous alternative rock, indie freedom, joyous filipino alternative rock, joyous japanese alternative rock, joyous korean alternative rock",
    "ESTP": "joyful hip-hop, joyful electronica, joyful filipino reggae, joyful japanese reggae, joyful korean reggae",
    "ESFP": "cheerful japanese pop, cheerful korean pop, cheerful japanese dance",
    "ENTP": "happy pop rock, joyful techno, happy japanese pop rock, happy korean pop rock",
    "ENFP": "joyful jazz, happy world, bright electronica, joyful funk",
    "ISTP": "cheerful punk, cheerful filipino punk, cheerful japanese punk, cheerful korean punk",
    "ISFP": "cheerful pop, cheerful filipino reggae, cheerful filipino pop, cheerful japanese pop, cheerful korean pop",
    "INTP": "cheerful punk, bright rock, cheerful metal, cheerful filipino punk, cheerful japanese punk, cheerful korean punk, bright filipino rock, bright japanese rock, bright korean rock",
    "INFP": "cheerful acoustic, cheerful pop, cheerful kpop, cheerful jpop" #added pop
  },
  "sad": {
    "ESTJ": "sad japanese hip-hop, sad korean hip-hop, sad japanese rock, sad korean rock", #sad filipino hip-hop melancholic patriotic, marching band despair  sad filipino rock
    "ENTJ": "sad classical, sad japanese rock, sad Korean rock", #jazz, eletronica, rock
    "ESFJ": "melancholic pop, sad blues, soulful sorrow, country heartbreak,sad korean blues",
    "ENFJ": "sad korean blues, sad japanese rnb, soulful sorrow, sad blues, sad korean pop ost",
    "ISTJ": "sad rock, melancholic oldies, sad japanese rock, sad korean rock",
    "ISFJ": "classical sorrow, religious mourning, sad japanese classical, sad korean classical",
    "INTJ": "sad classical, sad japanese classical, sad korean classical",
    "INFJ": "melancholic alternative rock, world of sadness, melancholic filipino alternative rock, melancholic japanese alternative rock, melancholic korean alternative rock",
    "ESTP": "sad classical, sad japanese classical, sad korean classical", #not hiphop or metal or rap
    "ESFP": "sad pop, ambient sorrow, melancholic blues, sad japanese pop, sad korean pop",
    "ENTP": "sad melancholic classical, tragic classical piano",
    "ENFP": "sad jazz, melancholy ambient, mournful blues, sad korean blues",
    "ISTP": "sad melancholic punk, sad melancholic korean punk",
    "ISFP": "sad pop, sad melancholic korean pop, sad japanese melancholic pop",
    "INTP": "melancholic punk, melancholic rock, melancholic metal, melancholic japanese punk, melancholic korean punk, melancholic filipino rock, melancholic japanese rock, melancholic korean rock",
    "INFP": "sad melancholic punk, sad japanese punk, sad korean punk, melancholic japanese rock, melancholic korean rock"
  },
  "surprise": {
    "ESTJ": "unexpected rhythm filipino hip-hop, unexpected rhythm japanese hip-hop, unexpected rhythm korean hip-hop, unexpected rhythm marching band, unexpected rhythm filipino rock, unexpected rhythm japanese rock, unexpected rhythm korean rock",
    "ENTJ": "unexpected rhythm japanese jazz, unexpected rhythm korean jazz, unexpected rhythm japanese classical, unexpected rhythm korean classical, unexpected rhythm rock",
    "ESFJ": "unconventional rhythm korean pop, unconventional rhythm japanese pop, unconventional rhythm japanese blues, jarring rhythm korean blues",
    "ENFJ": "unexpected rhythm filipino jazz, unexpected rhythm japanese jazz, unexpected rhythm korean jazz, unexpected rhythm pop, unexpected rhythm world",
    "ISTJ": "unexpected rhythm filipino classic rock, unexpected rhythm japanese classic rock, unexpected rhythm korean classic rock, unexpected rhythm intriguing oldies",
    "ISFJ": "unexpected rhythm japanese classical, unexpected rhythm korean classical, unexpected rhythm tranquil wonder",
    "INTJ": "unexpected rhythm japanese classical, unexpected rhythm korean classical, unexpected rhythm filipino rock, unexpected rhythm japanese rock, unexpected rhythm korean rock, unexpected rhythm metal",
    "INFJ": "unexpected rhythm filipino alternative rock, unexpected rhythm japanese alternative rock, unexpected rhythm korean alternative rock, unexpected rhythm indie",
    "ESTP": "unexpected rhythm filipino reggae, unexpected rhythm japanese reggae, unexpected rhythm korean reggae, unexpected rhythm filipino metal, unexpected rhythm japanese metal, unexpected rhythm korean metal, unexpected rhythm filipino hip-hop, unexpected rhythm japanese hip-hop, unexpected rhythm korean hip-hop, unexpected rhythm rap",
    "ESFP": "unexpected rhythm japanese pop, unexpected rhythm korean pop, unexpected rhythm filipino ambient, unexpected rhythm japanese ambient, unexpected rhythm korean ambient, unexpected rhythm surprised joy",
    "ENTP": "unexpected rhythm japanese classical, unexpected rhythm korean classical, unexpected rhythm japanese rock, unexpected rhythm korean rock, unexpected rhythm punk",
    "ENFP": "unexpected rhythm filipino jazz, unexpected rhythm japanese jazz, unexpected rhythm korean jazz, unexpected rhythm filipino ambient, unexpected rhythm japanese ambient, unexpected rhythm korean ambient, unexpected rhythm electronica, unexpected rhythm filipino blues, unexpected rhythm japanese blues, unexpected rhythm korean blues",
    "ISTP": "unexpected rhythm filipino punk, unexpected rhythm japanese punk, unexpected rhythm korean punk",
    "ISFP": "unexpected rhythm filipino reggae, unexpected rhythm japanese reggae, unexpected rhythm korean reggae, unexpected rhythm filipino pop, unexpected rhythm japanese pop, unexpected rhythm korean pop, unexpected rhythm ambient surprise",
    "INTP": "unexpected rhythm filipino punk, unexpected rhythm japanese punk, unexpected rhythm korean punk, unexpected rhythm filipino rock, unexpected rhythm japanese rock, unexpected rhythm korean rock, unexpected rhythm metal",
    "INFP": "unexpected rhythm filipino punk, unexpected rhythm japanese punk, unexpected rhythm korean punk, unexpected rhythm filipino rock, unexpected rhythm japanese rock, unexpected rhythm korean rock, unexpected rhythm alternative rock"
  },
  "neutral": {
    "ESTJ": "calm filipino hip-hop, neutral japanese hip-hop, neutral korean hip-hop, neutral marching band, calm filipino rock, neutral japanese rock, neutral korean rock",
    "ENTJ": "neutral jazz, neutral classical, smooth japanese jazz, smooth korean jazz, neutral filipino classical, neutral japanese classical, neutral korean classical",#neutral electronica
    "ESFJ": "calm pop, smooth blues, neutral soulful, calm filipino pop, calm japanese pop, calm korean pop, smooth filipino blues, smooth japanese blues, smooth korean blues",
    "ENFJ": "smooth jazz, calm blues, calm world, calm pop",
    "ISTJ": "neutral classic rock, smooth oldies, calm filipino classic rock, calm japanese classic rock, calm korean classic rock",
    "ISFJ": "smooth classical, peaceful wonder, neutral filipino classical, neutral japanese classical, neutral korean classical",
    "INTJ": "calm classical, smooth rock, neutral metal, smooth japanese classical, smooth korean classical, neutral japanese rock, neutral korean rock",
    "INFJ": "neutral japanese alternative rock, neutral korean alternative rock",
    "ESTP": "neutral reggae, neutral metal, calm hip-hop, smooth rap, neutral filipino reggae, neutral japanese reggae, neutral korean reggae, calm filipino metal, calm japanese metal, calm korean metal",
    "ESFP": "calm pop, peaceful ambient, neutral joy, calm filipino pop, calm japanese pop, calm korean pop, peaceful filipino ambient, peaceful japanese ambient, peaceful korean ambient",
    "ENTP": "smooth classical, chill rock, smooth punk, chill japanese classical, chill korean classical, smooth filipino rock, smooth japanese rock, smooth korean rock",
    "ENFP": "calm jazz, peaceful ambient, smooth electronica, neutral blues, neutral hip-hop, calm filipino jazz, calm japanese jazz, calm korean jazz, peaceful filipino ambient, peaceful japanese ambient, peaceful korean ambient",
    "ISTP": "smooth calm punk, smooth calm japanese punk, smooth calm korean punk",
    "ISFP": "ambient calm, smooth pop, ambient filipino calm, ambient japanese calm, ambient korean calm",
    "INTP": "neutral punk, smooth rock, calm japanese metal, calm korean punk",
    "INFP": "neutral punk, calm acoustic, calm japanese acoustic, calm korena acoustic"
  }
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

    full_search_terms = emotion_to_search_term.get(emotion, {}).get(personality_type, "chill vibes")
    individual_terms = [term.strip() for term in full_search_terms.split(',')]

    # Pick 3 unique random terms
    random_terms = random.sample(individual_terms, min(5, len(individual_terms)))
    print(f"Selected search terms: {random_terms}")

    all_tracks = []

    for term in random_terms:
        params = {
            'q': term,
            'type': 'track',
            'limit': 9,  # lower per search to keep total around 45
       #     'market': 'US'  # Adjust if needed
        }

        response = requests.get(f"{SPOTIFY_API_BASE_URL}/search", headers=headers, params=params)
        if response.status_code == 200:
            tracks = response.json().get('tracks', {}).get('items', [])
            all_tracks.extend(tracks)
        else:
            print(f"Error for term '{term}': {response.status_code} - {response.text}")

    print(f"Fetched {len(all_tracks)} raw tracks from all terms.")

    # Exclude unwanted artists
    excluded_keywords = ['upbeat', 'kids', 'uplifting', 'melodality', 'uniquesound', 'commentary', 'audiosphere', 'morninglightmusic', 'david schweitzer',
                         'tropical depression', 'masayuki suzuki', 'kanye west', 'biv', 'lullaby', 'romansenykmusic', 'junai kaden', 'sound ideas',
                         'rapunzel asmr', 'arjun', 'tubero', 'new politics', 'fishbone', 'bass boosted hd', 'boyinaband', 'gilang sadewa', 'the bangles',
                         'burnett and pentek', 'barbara cook', 'mido', 'nepsydaz']
    filtered_tracks = [
        track for track in all_tracks
        if not any(
            keyword in artist['name'].lower()
            for artist in track['artists']
            for keyword in excluded_keywords
        )
    ]

    # Deduplicate by track ID
    unique_tracks = {track['id']: track for track in filtered_tracks}.values()

    # Sort by popularity
    sorted_tracks = sorted(unique_tracks, key=lambda x: x['popularity'], reverse=True)

    # Shuffle a bit for variety
    random.shuffle(sorted_tracks)

    return [
        {
            'id': track['id'],
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'cover_url': track['album']['images'][0]['url'] if track['album']['images'] else '',
            'popularity': track['popularity']
        }
        for track in sorted_tracks
    ]



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



