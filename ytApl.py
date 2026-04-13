"""
YouTube Playlist Song Adder
============================
Add a list of song to a YouTube playlist.

Dependence:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

Setup:
    1. Go to https://console.cloud.google.com/
    2. Crete a project and add "YouTube Data API v3"
    3. Create credential OAuth 2.0 (type: Desktop App)
    4. Download the file client_secret.json in the same dir of this script
"""

import os
import json
import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# ─────────────────────────────────────────────
# CONFIGURATION — change these values
# ─────────────────────────────────────────────

PLAYLIST_ID = "PLXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # ID of your YouTube playlist

SONGS_FILE = "song.txt"  # file txt whit one song for line

CLIENT_SECRETS_FILE = "client_secret.json"   # file downloaded from Google Cloud Console
TOKEN_FILE = "token.json"                     # automatically generated at first login
SCOPES = ["https://www.googleapis.com/auth/youtube"]

MAX_RESULTS_SEARCH = 5   # how many results to consider for each search (increment this if you can't find the song)
DELAY_BETWEEN_REQUESTS = 1  # seconds between the request (avoid rate limiting)

# ─────────────────────────────────────────────


def load_songs(filepath: str) -> list[str]:
    """Reads songs from a txt file (one per line, ignores blank lines and comments)."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"File '{filepath}' not found.\n"
            "Create a txt file with one song per line in the same folder as the script"
        )
    with open(filepath, "r", encoding="utf-8") as f:
        songs = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
    if not songs:
        raise ValueError(f"The file '{filepath}' it's empty or it does not contain any valid songs.")
    return songs


def authenticate() -> object:
    """Authenticates the user and returns the YouTube service."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"File '{CLIENT_SECRETS_FILE}' not found.\n"
                    "Download it from Google Cloud Console → Credentials → OAuth 2.0."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def search_video(youtube, query: str) -> dict | None:
    """
    Searches for a video on YouTube and returns the first relevant result.
    Returns a dict with 'video_id' and 'title', or None if not found.
    """
    try:
        response = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=MAX_RESULTS_SEARCH,
            type="video",
            videoCategoryId="10",  # category Song
        ).execute()

        items = response.get("items", [])
        if not items:
            return None

        best = items[0]
        return {
            "video_id": best["id"]["videoId"],
            "title": best["snippet"]["title"],
            "channel": best["snippet"]["channelTitle"],
        }

    except HttpError as e:
        print(f"  ✗ Search error '{query}': {e}")
        return None


def add_to_playlist(youtube, playlist_id: str, video_id: str) -> bool:
    """Add a video to the playlist. Returns True if successful."""
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            },
        ).execute()
        return True

    except HttpError as e:
        error_content = json.loads(e.content)
        reason = error_content["error"]["errors"][0].get("reason", "unknown")

        if reason == "videoAlreadyInPlaylist":
            print("  ⚠  Video already in playlist, skipped.")
        elif reason == "playlistNotFound":
            print(f"  ✗ Playlist '{playlist_id}' not found. Check the ID..")
        else:
            print(f"  ✗ Adding error: {reason}")
        return False


def get_playlist_info(youtube, playlist_id: str) -> str:
    """Retrieve playlist title."""
    try:
        res = youtube.playlists().list(part="snippet", id=playlist_id).execute()
        items = res.get("items", [])
        if items:
            return items[0]["snippet"]["title"]
    except HttpError:
        pass
    return playlist_id


def main():
    print("=" * 55)
    print("  YouTube Playlist Song Adder")
    print("=" * 55)

    # Carica le canzoni dal file
    print(f"\n📄 Reading songs from file '{SONGS_FILE}'...")
    songs = load_songs(SONGS_FILE)
    print(f"  ✓ {len(songs)} songs finded.")

    # Autenticazione
    print("\n🔐 Authentication in progress...")
    youtube = authenticate()
    print("  ✓ Authenticated successfully!\n")

    # Info playlist
    playlist_title = get_playlist_info(youtube, PLAYLIST_ID)
    print(f"🎵 Destination playlist: {playlist_title}")
    print(f"   ({PLAYLIST_ID})\n")
    print("-" * 55)

    results = {"ok": [], "not_found": [], "error": []}

    for i, song in enumerate(songs, 1):
        print(f"\n[{i}/{len(songs)}] Search: \"{song}\"")

        # Cerca il video
        video = search_video(youtube, song)
        if not video:
            print(f"  ✗ No videos found for '{song}'")
            results["not_found"].append(song)
            continue

        print(f"  → Found: {video['title']} — {video['channel']}")
        print(f"     https://youtu.be/{video['video_id']}")

        # Aggiunge alla playlist
        success = add_to_playlist(youtube, PLAYLIST_ID, video["video_id"])
        if success:
            print("  ✓ Added at playlist!")
            results["ok"].append({"query": song, **video})
        else:
            results["error"].append(song)

        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Riepilogo finale
    print("\n" + "=" * 55)
    print("  RECAP")
    print("=" * 55)
    print(f"  ✓ Added successfully : {len(results['ok'])}")
    print(f"  ✗ Not found          : {len(results['not_found'])}")
    print(f"  ✗ Error              : {len(results['error'])}")

    if results["not_found"]:
        print("\nSong not found:")
        for s in results["not_found"]:
            print(f"  - {s}")

    if results["error"]:
        print("\nSong whit error:")
        for s in results["error"]:
            print(f"  - {s}")

    print("\nFinsh! 🎉")
    os.remove(percorso_file)

if __name__ == "__main__":
    main()
