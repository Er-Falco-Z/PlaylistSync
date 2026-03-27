# PlaylistSync 🎵

Export your **Spotify** liked songs and import them into **Tidal**, preserving the original order.

Built to fix the messy playlists that TuneMyMusic creates.

---

## Files

| File | Description |
|------|-------------|
| `spotify_export.py` | Exports Spotify Liked Songs to a JSON file |
| `tidal_import.py` | Imports the JSON into Tidal with detailed match logging |
| `tidal_clear_favorites.py` | Removes all tracks from Tidal favorites |
| `tidal_check_and_clear.py` | Diagnoses the Tidal account and optionally clears favorites (use it if `tidal_clear_favorites.py` don't remove all song) |

---

## Requirements

```bash
python -m pip install spotipy tidalapi python-dotenv
```

---

## Setup

### Spotify Credentials

1. Go to Spotify Developer
2. Create a new app
3. Add your Redirect URI in the app settings (ex.. `http://127.0.0.1:5000/callback`(from 2025 it don't accept the localhost))
4. Create a `.env` file in the project folder:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback
```

> ⚠️ If your Tidal password contains `#`, wrap it in quotes in the `.env` file

### Tidal Credentials

No configuration needed — on first run, the Tidal OAuth login will open automatically in your browser. The session is saved to `tidal_session.json` for subsequent runs.

---

## Usage

### 1. Export from Spotify

```bash
python spotify_export.py
```

Your browser will open to authorize the app. Generates `spotify_liked_songs.json` with all your saved tracks, ordered from most recent to oldest.

### 2. Import into Tidal

```bash
python tidal_import.py
```

On startup, it asks how to handle duplicates:
- `1` — skip tracks already in favorites (faster)
- `2` — re-add everything regardless

When done, it generates:
- `tidal_match_log.json` — full log of every match
- `tidal_not_found.json` — tracks not found on Tidal (only if any)

### 3. Clear Tidal Favorites

```bash
python tidal_clear_favorites.py
```

> ⚠️ This operation is irreversible. You must type `CONFERMA` to confirm. Runs in a loop until the list is completely empty.

### 4. Diagnose Tidal Account

```bash
python tidal_check_and_clear.py
```

Shows account info (username, ID, country) and the first 3 favorite tracks. Also offers the option to clear all favorites.

---

## How Matching Works

`tidal_import.py` uses two methods to find tracks on Tidal, in order of priority:

| Priority | Method | Reliability |
|----------|--------|-------------|
| 1 | **ISRC** — universal track identifier | ~99% |
| 2 | **Title + Artist** — fallback when ISRC finds nothing | variable |

### Reading the terminal output

- `✅ [ISRC]` → perfect match
- `✅ [TitleArtist]` → matched by title and artist, same name
- `⚠️ different title! [TitleArtist]` → something was found but with a different name, might be the wrong version
- `❌ not found` → track doesn't exist on Tidal or the name is too different

### Why some tracks are matched incorrectly

- Tidal has a different version (e.g. Remastered) compared to Spotify → different ISRC
- The title on Tidal is slightly different (e.g. with/without "feat.")
- The track is not available in your country
- The track has been removed from the Tidal catalog

---

## Generated Files

| File | Contents |
|------|----------|
| `spotify_liked_songs.json` | Full list of Spotify tracks with metadata (ISRC, title, artist, album, date added) |
| `tidal_match_log.json` | Per-track log: match method, title found on Tidal, alternative candidates |
| `tidal_not_found.json` | Tracks not found on Tidal, to be searched manually |
| `tidal_session.json` | Saved Tidal session, reloaded automatically on subsequent runs |

---

## Notes

- The Tidal API used is **unofficial** (reverse engineered) — it may break if Tidal changes their API
- Track order is preserved by inserting tracks from oldest to newest, so the final order on Tidal matches the original Spotify order
