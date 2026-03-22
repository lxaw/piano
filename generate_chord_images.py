#!/usr/bin/env python3
"""Generate keyboard diagram images with highlighted keys for all chords."""

import os
import sys

# Reuse the keyboard drawing from generate_keyboard_images
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_keyboard_images import draw_keyboard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHORDS_DIR = os.path.join(BASE_DIR, "assets", "chords")

NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

CHORD_TYPES = {
    "major":      [0, 4, 7],
    "minor":      [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented":  [0, 4, 8],
    "dominant7":  [0, 4, 7, 10],
    "major7":     [0, 4, 7, 11],
    "minor7":     [0, 3, 7, 10],
}

# Display names for chord types
CHORD_DISPLAY = {
    "major": "Major",
    "minor": "Minor",
    "diminished": "Dim",
    "augmented": "Aug",
    "dominant7": "Dom7",
    "major7": "Maj7",
    "minor7": "Min7",
}

BASE_OCTAVE_MIDI = 60  # C4

def main():
    count = 0
    for root_idx, root_name in enumerate(NOTE_NAMES):
        for chord_type, intervals in CHORD_TYPES.items():
            folder_name = f"{root_name}_{chord_type}"
            chord_dir = os.path.join(CHORDS_DIR, folder_name)

            root_midi = BASE_OCTAVE_MIDI + root_idx
            midi_notes = {root_midi + interval for interval in intervals}

            display = f"{root_name} {CHORD_DISPLAY[chord_type]}"
            output_path = os.path.join(chord_dir, "keyboard.png")
            draw_keyboard(midi_notes, output_path, label=display)
            print(f"  {folder_name} -> keyboard.png")
            count += 1

    print(f"\nDone! Generated {count} chord keyboard images.")

if __name__ == "__main__":
    main()
