"""
spotify_export.py
-----------------
Read the README.md in the repo for instructions.
"""

import json
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()

# --- Autenticazione ---
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="user-library-read",
    cache_path=".spotify_cache"
))

def get_all_liked_songs():
    """
    Recupera tutti i brani salvati, paginando l'API (max 50 per chiamata).
    Restituisce una lista ordinata dal più recente al più vecchio.
    """
    tracks = []
    limit = 50
    offset = 0

    print("⏳ Recupero brani da Spotify...")

    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = results.get("items", [])

        if not items:
            break

        for item in items:
            track = item["track"]
            added_at = item["added_at"]

            # Gestisce i casi in cui un brano è stato rimosso dal catalogo
            if track is None:
                continue

            tracks.append({
                "position": len(tracks) + 1,          # posizione 1-based nell'elenco
                "added_at": added_at,                  # data aggiunta (ISO 8601)
                "title": track["name"],
                "artist": ", ".join(a["name"] for a in track["artists"]),
                "album": track["album"]["name"],
                "isrc": track.get("external_ids", {}).get("isrc"),  # ID universale → usato per matchare su Tidal
                "spotify_id": track["id"],
                "duration_ms": track["duration_ms"],
                "explicit": track["explicit"],
            })

        print(f"  → Recuperati {len(tracks)} brani finora...")
        offset += limit

        # Rispetta il rate limit di Spotify
        time.sleep(0.1)

    print(f"\n✅ Totale brani trovati: {len(tracks)}")
    return tracks


def save_to_json(tracks, filename="spotify_liked_songs.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)
    print(f"💾 Salvato in '{filename}'")


if __name__ == "__main__":
    songs = get_all_liked_songs()
    save_to_json(songs)

    # Preview dei primi 5
    print("\n📋 Primi 5 brani:")
    for s in songs[:5]:
        print(f"  {s['position']:4}. {s['artist']} — {s['title']}  [{s['isrc'] or 'no ISRC'}]")
