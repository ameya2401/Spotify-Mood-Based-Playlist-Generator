from flask import Flask, render_template, request, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

CLIENT_ID = "95ac955f48bb465295719fd2f0aa24ba"
CLIENT_SECRET = "1e5fb91e5b594c9abc0fc0e47f434173"
REDIRECT_URI = "http://localhost:8888/callback"

scope = "user-library-read playlist-modify-public"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope,
    )
)


def get_user_playlists():
    playlists = []
    results = sp.current_user_playlists()
    while results:
        for item in results["items"]:
            playlists.append((item["id"], item["name"]))
        if results["next"]:
            results = sp.next(results)
        else:
            break
    return playlists


def get_tracks_from_playlist(playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    while results:
        for item in results["items"]:
            track = item["track"]
            if track:  # Ensure that the track is not None
                tracks.append(track)
        if results["next"]:
            results = sp.next(results)
        else:
            break
    return tracks


def filter_tracks_by_mood(tracks, mood):
    filtered_tracks = []
    for track in tracks:
        track_id = track["id"]

        # Check if track_id is valid before getting audio features
        if track_id:
            features = sp.audio_features(track_id)[
                0
            ]  # Get audio features for the track
            if features:  # Ensure features are retrieved successfully
                if (
                    mood == "happy"
                    and features["energy"] >= 0.7
                    and features["valence"] >= 0.6
                ):
                    filtered_tracks.append(track_id)
                elif (
                    mood == "sad"
                    and features["energy"] < 0.4
                    and features["valence"] < 0.4
                ):
                    filtered_tracks.append(track_id)
                elif (
                    mood == "relaxed"
                    and features["tempo"] < 100
                    and features["energy"] < 0.5
                ):
                    filtered_tracks.append(track_id)
    return filtered_tracks


def create_mood_playlist(selected_playlist_id, mood):
    user_id = sp.current_user()["id"]
    playlist_name = f"{mood.capitalize()} Vibes"
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)

    # Fetch tracks from the selected playlist
    original_tracks = get_tracks_from_playlist(selected_playlist_id)

    # Filter tracks based on the selected mood
    track_ids = filter_tracks_by_mood(original_tracks, mood)

    if track_ids:
        sp.playlist_add_items(playlist_id=playlist["id"], items=track_ids)
        return playlist["name"]
    else:
        return "No tracks found for this mood."


@app.route("/")
def index():
    playlists = get_user_playlists()
    return render_template("playlist_selection.html", playlists=playlists)


@app.route("/tracks", methods=["POST"])
def show_tracks():
    selected_playlist_id = request.form["selected_playlist_id"]
    original_tracks = get_tracks_from_playlist(selected_playlist_id)
    return render_template(
        "track_display.html",
        tracks=original_tracks,
        selected_playlist_id=selected_playlist_id,
    )


@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    mood = request.form["mood"].lower()
    selected_playlist_id = request.form["selected_playlist_id"]
    playlist_name = create_mood_playlist(selected_playlist_id, mood)
    return render_template("congratulations.html", playlist=playlist_name)


if __name__ == "__main__":
    app.run(debug=True)
