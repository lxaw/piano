#!/usr/bin/env python3
"""Create Anki cards for all 88 piano notes.

Card format:
  Front: staff image + audio plays
  Back:  note name (e.g. A1)

Requires Anki open with AnkiConnect add-on installed.
"""

import os
import sys
from time import sleep

from anki_commands import invoke

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.join(BASE_DIR, "assets", "notes")

# ─── Config ───────────────────────────────────────────────────────────────────

DECK_NAME = "Piano::Notes"
MODEL_NAME = "PianoNote"

CARD_CSS = """\
.card {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 24px;
    text-align: center;
    color: #333;
    background-color: #fafafa;
    padding: 20px;
}
.card img {
    max-width: 400px;
    margin: 10px auto;
    display: block;
}
.note-name {
    font-size: 48px;
    font-weight: bold;
    color: #2a6dd9;
    margin: 20px 0;
}
"""

FRONT_TEMPLATE = """\
<div class="card">
{{Staff}}
<br>
{{Audio}}
</div>
"""

BACK_TEMPLATE = """\
<div class="card">
{{FrontSide}}
<hr id="answer">
<div class="note-name">{{NoteName}}</div>
{{Keyboard}}
</div>
"""


# ─── Setup ────────────────────────────────────────────────────────────────────

def ensure_deck():
    invoke("createDeck", deck=DECK_NAME)
    print(f"Deck '{DECK_NAME}' ready.")


def ensure_model():
    """Create the note type if it doesn't already exist."""
    existing = invoke("modelNames")
    if MODEL_NAME in existing:
        print(f"Model '{MODEL_NAME}' already exists.")
        return

    invoke("createModel",
        modelName=MODEL_NAME,
        inOrderFields=["NoteName", "Staff", "Keyboard", "Audio"],
        css=CARD_CSS,
        cardTemplates=[{
            "Name": "Staff → Note Name",
            "Front": FRONT_TEMPLATE,
            "Back": BACK_TEMPLATE,
        }],
    )
    print(f"Model '{MODEL_NAME}' created.")


# ─── Card creation ────────────────────────────────────────────────────────────

def create_note_card(note_name):
    """Create a single Anki card for a piano note."""
    note_dir = os.path.join(NOTES_DIR, note_name)
    if not os.path.isdir(note_dir):
        raise FileNotFoundError(f"Note folder not found: {note_dir}")

    staff_path = os.path.join(note_dir, "staff.png")
    keyboard_path = os.path.join(note_dir, "keyboard.png")
    audio_path = os.path.join(note_dir, "audio.mp3")

    # File basenames for Anki media
    staff_filename = f"piano_note_{note_name}_staff.png"
    keyboard_filename = f"piano_note_{note_name}_keyboard.png"
    audio_filename = f"piano_note_{note_name}_audio.mp3"

    note = {
        "deckName": DECK_NAME,
        "modelName": MODEL_NAME,
        "fields": {
            "NoteName": note_name,
            "Staff": f'<img src="{staff_filename}">',
            "Keyboard": f'<img src="{keyboard_filename}">',
            "Audio": f"[sound:{audio_filename}]",
        },
        "options": {"allowDuplicate": False},
        "picture": [],
        "audio": [],
    }

    # Attach staff image
    if os.path.exists(staff_path):
        note["picture"].append({
            "path": os.path.abspath(staff_path),
            "filename": staff_filename,
            "fields": [],  # already referenced in the field HTML
        })

    # Attach keyboard image
    if os.path.exists(keyboard_path):
        note["picture"].append({
            "path": os.path.abspath(keyboard_path),
            "filename": keyboard_filename,
            "fields": [],
        })

    # Attach audio
    if os.path.exists(audio_path):
        note["audio"].append({
            "path": os.path.abspath(audio_path),
            "filename": audio_filename,
            "fields": [],
        })

    invoke("addNote", note=note)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Get all note folders sorted by MIDI order
    NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

    all_notes = []
    for midi_num in range(21, 109):  # A0 to C8
        note_idx = midi_num % 12
        octave = (midi_num // 12) - 1
        name = f"{NOTE_NAMES[note_idx]}{octave}"
        all_notes.append(name)

    print(f"Found {len(all_notes)} notes to process.\n")

    ensure_deck()
    ensure_model()

    errors = []
    for i, note_name in enumerate(all_notes, 1):
        try:
            create_note_card(note_name)
            print(f"  [{i}/{len(all_notes)}] {note_name} ✓")
        except Exception as e:
            err_msg = str(e)
            if "duplicate" in err_msg.lower():
                print(f"  [{i}/{len(all_notes)}] {note_name} (skipped, already exists)")
            else:
                print(f"  [{i}/{len(all_notes)}] {note_name} ✗ — {e}")
                errors.append(note_name)
        sleep(0.05)  # small delay to not overwhelm AnkiConnect

    print(f"\nDone! Created cards for {len(all_notes) - len(errors)}/{len(all_notes)} notes.")
    if errors:
        print(f"Errors: {', '.join(errors)}")


if __name__ == "__main__":
    main()
