# YouTube Playlist Song Adder

A Python script that searches for a list of songs on YouTube and automatically adds them to a playlist.

## Requirements

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
```

## Setup

### 1. Google Cloud credentials
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project and enable the **YouTube Data API v3**
3. Go to **Credentials → Create Credentials → OAuth 2.0 Client ID** (type: Desktop App)
4. Download the file and rename it to `client_secret.json`, then place it in the project folder
5. In **OAuth consent screen → Test users**, add your Google account

### 2. Configure the playlist
```bash
cp .env.example .env
```
Edit `.env` and set your `PLAYLIST_ID`. You can find it in the playlist URL:
`https://www.youtube.com/playlist?list=`**`YOUR_PLAYLIST_ID`**

### 3. Add your songs
Edit `songs.txt` — one song per line. Lines starting with `#` are treated as comments.

```
# My playlist
Bohemian Rhapsody Queen
Hotel California Eagles
Stairway to Heaven Led Zeppelin
```

## Usage

```bash
python3 youtube_playlist_adder.py
```

On first run, a browser window will open for Google login. The token is saved to `token.json` for subsequent runs.

## Project structure

```
.
├── youtube_playlist_adder.py   # main script
├── songs.txt                   # your song list
├── client_secret.json          # OAuth credentials (do NOT commit)
├── token.json                  # auto-generated after first login (do NOT commit)
├── .env                        # your playlist ID (do NOT commit)
└── .env.example                # template for .env
```
