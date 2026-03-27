"""
tidal_clear_favorites.py
------------------------
Read the README.md in the repo for instructions.
"""

import time
import tidalapi
from pathlib import Path

SESSION_FILE = "tidal_session.json"
DELAY_BETWEEN_REMOVES = 0.3  # secondi tra una rimozione e l'altra


def get_tidal_session() -> tidalapi.Session:
    session = tidalapi.Session()
    

    if Path(SESSION_FILE).exists():
        try:
            session.load_session_from_file(Path(SESSION_FILE))
            if session.check_login():
                print("✅ Sessione Tidal caricata.")
                return session
        except Exception:
            print("⚠️  Sessione scaduta, nuovo login necessario.")

    session.login_oauth_simple()
    session.save_session_to_file(Path(SESSION_FILE))
    print("✅ Login Tidal completato.")
    return session


def main():
    session = get_tidal_session()

    #print(f"User ID script: {session.user.id}")
    #print(f"Session ID: {session.session_id[:8]}...")  # primi 8 char per sicurezza
    #print(f"Login OK: {session.check_login()}")  # True se valido

    # === TEST ACCOUNT E PREFERITI ===
me = session.user
print(f"📱 Account script: '{me.name}' (ID: {me.id})")
print(f"Paese: {getattr(me, 'country_code', '??')}")

# Test preferiti
tracks = me.favorites.tracks(limit=5)
if tracks:
    print("🎵 Primi preferiti script:")
    for t in tracks:
        print(f"  - {t.name} di {t.artist.name}")
else:
    print("ℹ️ Script vede 0 preferiti")
print()  # riga vuota
# === FINE TEST ===

    # Recupera tutti i preferiti
    print("\n🔍 Recupero brani preferiti da Tidal...")
    try:
        tracks = []
        offset = 0
        limit = 50
        while True:
            batch = session.user.favorites.tracks(limit=limit, offset=offset)
            if not batch:
                break
            tracks.extend(batch)
            print(f"  → Recuperati {len(tracks)} brani finora...")
            offset += limit
            if len(batch) < limit:
                break
    except Exception as e:
        print(f"❌ Errore nel recupero dei preferiti: {e}")
        return

    total = len(tracks)
    if total == 0:
        print("ℹ️  Nessun brano nei preferiti, niente da fare.")
        return

    print(f"⚠️  Trovati {total} brani nei preferiti.")
    print("\n🚨 ATTENZIONE: questa operazione rimuoverà TUTTI i brani preferiti da Tidal.")
    print("   Non è possibile annullare l'operazione.\n")

    conferma = input(f"Scrivi CONFERMA per procedere: ").strip()
    if conferma != "CONFERMA":
        print("❌ Operazione annullata.")
        return

    rimossi = 0
    errori  = 0

    print(f"\n🗑️  Inizio rimozione in loop finché non sono finiti tutti...\n")

    while True:
        # Ricarica la lista ad ogni giro — Tidal aggiorna la lista dopo ogni rimozione
        try:
            tracks = session.user.favorites.tracks()
        except Exception as e:
            print(f"❌ Errore nel recupero: {e}")
            break

        if not tracks:
            break

        print(f"  → {len(tracks)} brani rimasti, rimuovo...")

        for track in tracks:
            title  = getattr(track, "name", "???")
            artist = getattr(track.artist, "name", "???") if hasattr(track, "artist") else "???"
            print(f"  🗑️  {artist} — {title}")

            try:
                session.user.favorites.remove_track(track.id)
                rimossi += 1
            except Exception as e:
                print(f"  ⚠️  errore: {e}")
                errori += 1

            time.sleep(DELAY_BETWEEN_REMOVES)

    print("\n" + "═" * 50)
    print(f"🗑️  Rimossi:  {rimossi}")
    print(f"⚠️  Errori:   {errori}")
    print("═" * 50)
    print("\n✅ Operazione completata!")

if __name__ == "__main__":
    main()