"""
tidal_import.py
---------------
Read the README.md in the repo for instructions.
"""
 
import json
import time
import tidalapi
from pathlib import Path
 
SESSION_FILE = "tidal_session.json"
INPUT_FILE   = "spotify_liked_songs.json"
LOG_FILE     = "tidal_match_log.json"
 
DELAY_BETWEEN_ADDS = 0.5
 
 
def get_tidal_session() -> tidalapi.Session:
    session = tidalapi.Session()
 
    if Path(SESSION_FILE).exists():
        try:
            session.load_session_from_file(Path(SESSION_FILE))
            if session.check_login():
                print("✅ Sessione Tidal caricata dal file.")
                return session
        except Exception:
            print("⚠️  Sessione scaduta, nuovo login necessario.")
 
    session.login_oauth_simple()
    session.save_session_to_file(Path(SESSION_FILE))
    print("✅ Login Tidal completato e sessione salvata.")
    return session
 
 
def search_by_isrc(session: tidalapi.Session, isrc: str):
    try:
        results = session.search(isrc, models=[tidalapi.Track])
        tracks = results.get("tracks", [])
        for t in tracks:
            if hasattr(t, "isrc") and t.isrc and t.isrc.upper() == isrc.upper():
                return t
    except Exception:
        pass
    return None
 
 
def search_by_title_artist(session: tidalapi.Session, title: str, artist: str):
    try:
        query = f"{artist.split(',')[0].strip()} {title}"
        results = session.search(query, models=[tidalapi.Track], limit=5)
        tracks = results.get("tracks", [])
 
        if not tracks:
            return None, []
 
        candidates = []
        for t in tracks:
            candidates.append({
                "tidal_id":     t.id,
                "tidal_title":  t.name,
                "tidal_artist": t.artist.name if hasattr(t, "artist") else "?",
                "tidal_album":  t.album.name if hasattr(t, "album") else "?",
                "tidal_isrc":   getattr(t, "isrc", None),
            })
 
        return tracks[0], candidates
    except Exception:
        pass
    return None, []
 
 
def add_to_favorites(session: tidalapi.Session, track: tidalapi.Track) -> bool:
    try:
        session.user.favorites.add_track(track.id)
        return True
    except Exception as e:
         print(f"    ⚠️  Errore aggiunta: {type(e).__name__}: {e}")
        return False
 
 
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        spotify_tracks = json.load(f)
 
    print(f"📂 Caricati {len(spotify_tracks)} brani da '{INPUT_FILE}'")
 
    session = get_tidal_session()
 
    # Chiede all'utente come gestire i duplicati
    print("\n❓ Come vuoi gestire i brani già presenti nei preferiti Tidal?")
    print("   1) Salta i duplicati (più veloce)")
    print("   2) Riaggiungili comunque (sovrascrive)")
    scelta = input("\nScelta (1/2): ").strip()
    salta_duplicati = scelta != "2"
 
    if salta_duplicati:
        print("\n🔍 Recupero preferiti esistenti su Tidal...")
        try:
            existing_ids = set()
            existing = session.user.favorites.tracks()
            for t in existing:
                if hasattr(t, "isrc") and t.isrc:
                    existing_ids.add(t.isrc.upper())
            print(f"  → {len(existing_ids)} brani già presenti (verranno saltati)")
        except Exception as e:
            print(f"  ⚠️  Non riuscito a recuperare preferiti esistenti: {e}")
            existing_ids = set()
    else:
        print("\n ℹ️  Modalità riaggiunta: i duplicati verranno aggiunti comunque.")
        existing_ids = set()
 
    ordered = list(reversed(spotify_tracks))
 
    added     = []
    skipped   = []
    not_found = []
    match_log = []
 
    print(f"\n🚀 Inizio importazione di {len(ordered)} brani su Tidal...\n")
 
    for i, song in enumerate(ordered, 1):
        title  = song["title"]
        artist = song["artist"]
        isrc   = song.get("isrc")
 
        print(f"[{i:4}/{len(ordered)}] {artist} — {title}", end="  ")
 
        log_entry = {
            "spotify_position": song["position"],
            "spotify_title":    title,
            "spotify_artist":   artist,
            "spotify_album":    song.get("album", ""),
            "spotify_isrc":     isrc,
            "status":           None,
            "match_method":     None,
            "tidal_title":      None,
            "tidal_artist":     None,
            "tidal_album":      None,
            "tidal_isrc":       None,
            "tidal_id":         None,
            "candidates":       [],
        }
 
        if salta_duplicati and isrc and isrc.upper() in existing_ids:
            print("⏭️  già presente")
            skipped.append(song)
            log_entry["status"] = "skipped_already_present"
            match_log.append(log_entry)
            continue
 
        tidal_track = None
        if isrc:
            tidal_track = search_by_isrc(session, isrc)
            if tidal_track:
                log_entry["match_method"] = "ISRC"
                log_entry["tidal_title"]  = tidal_track.name
                log_entry["tidal_artist"] = tidal_track.artist.name if hasattr(tidal_track, "artist") else "?"
                log_entry["tidal_album"]  = tidal_track.album.name if hasattr(tidal_track, "album") else "?"
                log_entry["tidal_isrc"]   = getattr(tidal_track, "isrc", None)
                log_entry["tidal_id"]     = tidal_track.id
 
        if tidal_track is None:
            tidal_track, candidates = search_by_title_artist(session, title, artist)
            log_entry["candidates"] = candidates
            if tidal_track:
                log_entry["match_method"] = "TitleArtist"
                log_entry["tidal_title"]  = tidal_track.name
                log_entry["tidal_artist"] = tidal_track.artist.name if hasattr(tidal_track, "artist") else "?"
                log_entry["tidal_album"]  = tidal_track.album.name if hasattr(tidal_track, "album") else "?"
                log_entry["tidal_isrc"]   = getattr(tidal_track, "isrc", None)
                log_entry["tidal_id"]     = tidal_track.id
 
        if tidal_track is None:
            print("❌ non trovato")
            not_found.append(song)
            log_entry["status"] = "not_found"
            match_log.append(log_entry)
            continue
 
        ok = add_to_favorites(session, tidal_track)
        if ok:
            title_match = tidal_track.name.lower().strip() == title.lower().strip()
            flag = "✅" if title_match else "⚠️  titolo diverso!"
            print(f"{flag}  [{log_entry['match_method']}] → {tidal_track.name}")
            added.append(song)
            log_entry["status"] = "added"
        else:
            log_entry["status"] = "error_adding"
            not_found.append(song)
 
        match_log.append(log_entry)
        time.sleep(DELAY_BETWEEN_ADDS)
 
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(match_log, f, ensure_ascii=False, indent=2)
 
    print("\n" + "═" * 50)
    print(f"✅ Aggiunti:        {len(added)}")
    print(f"⏭️  Già presenti:   {len(skipped)}")
    print(f"❌ Non trovati:    {len(not_found)}")
    print("═" * 50)
 
    title_matches = [e for e in match_log if e["match_method"] == "TitleArtist"]
    suspicious    = [e for e in title_matches
                     if e["tidal_title"] and e["spotify_title"].lower().strip() != e["tidal_title"].lower().strip()]
 
    print(f"\n📊 Match per ISRC (affidabili):          {len([e for e in match_log if e['match_method'] == 'ISRC'])}")
    print(f"📊 Match per titolo+artista:              {len(title_matches)}")
    print(f"⚠️  Di cui con titolo diverso (sospetti): {len(suspicious)}")
 
    if not_found:
        not_found_file = "tidal_not_found.json"
        with open(not_found_file, "w", encoding="utf-8") as f:
            json.dump(not_found, f, ensure_ascii=False, indent=2)
        print(f"\n📋 Brani non trovati → '{not_found_file}'")
 
    print(f"📋 Log completo di tutti i match → '{LOG_FILE}'")
    print("\n🎉 Importazione completata!")
 
 
if __name__ == "__main__":
    main()