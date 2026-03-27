"""
tidal_check_and_clear.py 
------------------------
Read the README.md in the repo for instructions.
"""

import time
import tidalapi
from pathlib import Path

SESSION_FILE = Path("tidal_session.json")

def get_session():
    session = tidalapi.Session()
    if SESSION_FILE.exists():
        try:
            session.load_session_from_file(SESSION_FILE)
            if session.check_login():
                print("✅ Sessione caricata")
                return session
        except:
            pass
    print("🔐 Nuovo login...")
    session.login_oauth_simple()
    session.save_session_to_file(SESSION_FILE)
    return session

session = get_session()
me = session.user

print("\n" + "="*60)
print(f"👤 ACCOUNT: '{me.username}' (ID: {me.id})")  # ← FIX: username
print(f"🌍 Paese: {getattr(me, 'country_code', '??')}")
print("="*60)

# Conta preferiti
tracks = session.user.favorites.tracks(limit=1000)
print(f"🎵 Brani preferiti: {len(tracks)}")

if len(tracks) > 0:
    print("\n📋 PRIMI 3:")
    for t in tracks[:3]:
        print(f"  - {t.name} — {t.artist.name}")

    conferma = input("\n🚨 Rimuovere TUTTI? (CONFERMA): ")
    if conferma == "CONFERMA":
        print("\n🗑️ Pulizia...")
        for i, track in enumerate(tracks, 1):
            try:
                session.user.favorites.remove_track(track.id)
                print(f"  {i}/{len(tracks)} ✓")
                time.sleep(0.2)
            except Exception as e:
                print(f"  {i}/{len(tracks)} ✗ {e}")
        print("\n✅ FATTO!")
    else:
        print("Annullato.")
else:
    print("ℹ️ Nessun brano.")