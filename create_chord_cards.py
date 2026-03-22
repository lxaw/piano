#!/usr/bin/env python3
"""Create Anki cards for all piano chords.

Two card types per chord:
  Card 1 (Staff → Name): Front = staff + audio, Back = chord name + fingerings
  Card 2 (Name → Fingering): Front = chord name + audio, Back = fingerings

Requires Anki open with AnkiConnect add-on installed.
"""

import os
from time import sleep

from anki_commands import invoke

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHORDS_DIR = os.path.join(BASE_DIR, "assets", "chords")

# ─── Config ───────────────────────────────────────────────────────────────────

DECK_NAME = "Piano::Chords"
MODEL_NAME = "PianoChord"

NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

CHORD_TYPES = {
    "major": "Major",
    "minor": "Minor",
    "diminished": "Dim",
    "augmented": "Aug",
    "dominant7": "Dom7",
    "major7": "Maj7",
    "minor7": "Min7",
}

CARD_CSS = """\
.card {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 20px;
    text-align: center;
    color: #333;
    background-color: #fafafa;
    padding: 20px;
}
.card img {
    max-width: 500px;
    margin: 8px auto;
    display: block;
}
.chord-name {
    font-size: 42px;
    font-weight: bold;
    color: #2a6dd9;
    margin: 16px 0;
}
.fingering-label {
    font-size: 16px;
    color: #666;
    margin: 4px 0;
}
.fingering-row {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 10px;
}
.fingering-row img {
    max-width: 400px;
}
.notes-info {
    font-size: 18px;
    color: #555;
    margin: 8px 0;
}
"""

# Card 1: Staff + Audio → Name + Fingerings
FRONT_STAFF = """\
<div class="card">
{{Staff}}
<br>
{{Audio}}
</div>
"""

BACK_STAFF = """\
<div class="card">
{{FrontSide}}
<hr id="answer">
<div class="chord-name">{{ChordName}}</div>
<div class="notes-info">{{Notes}}</div>
{{Keyboard}}
<div class="fingering-row">
<div>{{FingeringRH}}</div>
<div>{{FingeringLH}}</div>
</div>
<div class="fingering-label">RH: {{RHText}} &nbsp;|&nbsp; LH: {{LHText}}</div>
</div>
"""

# Card 2: Name + Audio → Fingerings
FRONT_NAME = """\
<div class="card">
<div class="chord-name">{{ChordName}}</div>
{{Audio}}
</div>
"""

BACK_NAME = """\
<div class="card">
{{FrontSide}}
<hr id="answer">
{{Staff}}
{{Keyboard}}
<div class="fingering-row">
<div>{{FingeringRH}}</div>
<div>{{FingeringLH}}</div>
</div>
<div class="fingering-label">RH: {{RHText}} &nbsp;|&nbsp; LH: {{LHText}}</div>
</div>
"""


# ─── Setup ────────────────────────────────────────────────────────────────────

def ensure_deck():
    invoke("createDeck", deck=DECK_NAME)
    print(f"Deck '{DECK_NAME}' ready.")


def ensure_model():
    existing = invoke("modelNames")
    if MODEL_NAME in existing:
        print(f"Model '{MODEL_NAME}' already exists.")
        return

    invoke("createModel",
        modelName=MODEL_NAME,
        inOrderFields=[
            "ChordName", "Notes",
            "Staff", "Keyboard", "Audio",
            "FingeringRH", "FingeringLH",
            "RHText", "LHText",
        ],
        css=CARD_CSS,
        cardTemplates=[
            {
                "Name": "Staff → Name + Fingering",
                "Front": FRONT_STAFF,
                "Back": BACK_STAFF,
            },
            {
                "Name": "Name → Fingering",
                "Front": FRONT_NAME,
                "Back": BACK_NAME,
            },
        ],
    )
    print(f"Model '{MODEL_NAME}' created.")


# ─── Parse info.txt ──────────────────────────────────────────────────────────

def parse_info(chord_dir):
    info_path = os.path.join(chord_dir, "info.txt")
    data = {}
    with open(info_path, "r") as f:
        for line in f:
            line = line.strip()
            if ": " in line:
                key, val = line.split(": ", 1)
                data[key] = val
    return data


# ─── Card creation ────────────────────────────────────────────────────────────

def create_chord_card(folder_name):
    chord_dir = os.path.join(CHORDS_DIR, folder_name)
    info = parse_info(chord_dir)

    chord_name = info.get("Chord", folder_name)
    notes = info.get("Notes", "")
    rh_text = info.get("RH Fingering", "")
    lh_text = info.get("LH Fingering", "")

    # Build display name: "C Major" instead of "C major"
    parts = chord_name.split()
    if len(parts) >= 2:
        display_name = f"{parts[0]} {CHORD_TYPES.get(parts[1], parts[1])}"
    else:
        display_name = chord_name

    # File paths
    staff_path = os.path.join(chord_dir, "staff.png")
    keyboard_path = os.path.join(chord_dir, "keyboard.png")
    audio_path = os.path.join(chord_dir, "audio.mp3")
    fing_rh_path = os.path.join(chord_dir, "fingering_rh.png")
    fing_lh_path = os.path.join(chord_dir, "fingering_lh.png")

    # Media filenames for Anki
    prefix = f"piano_chord_{folder_name}"
    staff_fn = f"{prefix}_staff.png"
    keyboard_fn = f"{prefix}_keyboard.png"
    audio_fn = f"{prefix}_audio.mp3"
    fing_rh_fn = f"{prefix}_fingering_rh.png"
    fing_lh_fn = f"{prefix}_fingering_lh.png"

    note = {
        "deckName": DECK_NAME,
        "modelName": MODEL_NAME,
        "fields": {
            "ChordName": display_name,
            "Notes": notes,
            "Staff": f'<img src="{staff_fn}">',
            "Keyboard": f'<img src="{keyboard_fn}">',
            "Audio": f"[sound:{audio_fn}]",
            "FingeringRH": f'<img src="{fing_rh_fn}">',
            "FingeringLH": f'<img src="{fing_lh_fn}">',
            "RHText": rh_text,
            "LHText": lh_text,
        },
        "options": {"allowDuplicate": False},
        "picture": [],
        "audio": [],
    }

    # Attach media files
    for path, fn in [
        (staff_path, staff_fn),
        (keyboard_path, keyboard_fn),
        (fing_rh_path, fing_rh_fn),
        (fing_lh_path, fing_lh_fn),
    ]:
        if os.path.exists(path):
            note["picture"].append({
                "path": os.path.abspath(path),
                "filename": fn,
                "fields": [],
            })

    if os.path.exists(audio_path):
        note["audio"].append({
            "path": os.path.abspath(audio_path),
            "filename": audio_fn,
            "fields": [],
        })

    invoke("addNote", note=note)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Build ordered list of chord folders
    all_chords = []
    for root_name in NOTE_NAMES:
        for chord_type in CHORD_TYPES:
            folder = f"{root_name}_{chord_type}"
            if os.path.isdir(os.path.join(CHORDS_DIR, folder)):
                all_chords.append(folder)

    print(f"Found {len(all_chords)} chords to process.")
    print(f"Each chord creates 2 cards → {len(all_chords) * 2} total cards.\n")

    ensure_deck()
    ensure_model()

    errors = []
    for i, folder in enumerate(all_chords, 1):
        try:
            create_chord_card(folder)
            print(f"  [{i}/{len(all_chords)}] {folder} ✓")
        except Exception as e:
            err_msg = str(e)
            if "duplicate" in err_msg.lower():
                print(f"  [{i}/{len(all_chords)}] {folder} (skipped, duplicate)")
            else:
                print(f"  [{i}/{len(all_chords)}] {folder} ✗ — {e}")
                errors.append(folder)
        sleep(0.05)

    total = len(all_chords)
    ok = total - len(errors)
    print(f"\nDone! Created {ok}/{total} chord notes ({ok * 2} cards).")
    if errors:
        print(f"Errors: {', '.join(errors)}")


if __name__ == "__main__":
    main()
