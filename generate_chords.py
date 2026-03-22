#!/usr/bin/env python3
"""Generate folders with audio and MIDI for all basic chord types across all 12 roots."""

import os
import subprocess
from midiutil import MIDIFile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "chords")
SOUNDFONT = os.path.join(BASE_DIR, "FluidR3_GM.sf2")

NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Chord types: name -> list of semitone intervals from root
CHORD_TYPES = {
    "major":      [0, 4, 7],
    "minor":      [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented":  [0, 4, 8],
    "dominant7":  [0, 4, 7, 10],
    "major7":     [0, 4, 7, 11],
    "minor7":     [0, 3, 7, 10],
}

# Use octave 4 as the base for chords (middle of the piano)
BASE_OCTAVE_MIDI = 60  # C4

def generate_chord_midi(midi_notes, output_path):
    """Generate a MIDI file with all notes of a chord played together."""
    midi = MIDIFile(1)
    midi.addTempo(0, 0, 120)
    midi.addProgramChange(0, 0, 0, 0)  # Acoustic Grand Piano
    for note in midi_notes:
        midi.addNote(0, 0, note, 0, 3, 90)  # 3 beats, velocity 90
    with open(output_path, "wb") as f:
        midi.writeFile(f)

def midi_to_wav(midi_path, wav_path):
    subprocess.run([
        "fluidsynth", "-ni", "-F", wav_path, "-r", "44100",
        SOUNDFONT, midi_path
    ], check=True, capture_output=True)

def wav_to_mp3(wav_path, mp3_path):
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path, "-b:a", "192k", mp3_path
        ], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    count = 0
    for root_idx, root_name in enumerate(NOTE_NAMES):
        for chord_type, intervals in CHORD_TYPES.items():
            # Folder name: e.g., C_major, Db_minor7
            folder_name = f"{root_name}_{chord_type}"
            chord_dir = os.path.join(ASSETS_DIR, folder_name)
            os.makedirs(chord_dir, exist_ok=True)

            # Calculate MIDI notes for this chord
            root_midi = BASE_OCTAVE_MIDI + root_idx
            midi_notes = [root_midi + interval for interval in intervals]

            # Save note info
            note_names = []
            for m in midi_notes:
                octave = (m // 12) - 1
                note_in_oct = m % 12
                note_names.append(f"{NOTE_NAMES[note_in_oct]}{octave}")

            # Write metadata
            with open(os.path.join(chord_dir, "info.txt"), "w") as f:
                f.write(f"Chord: {root_name} {chord_type}\n")
                f.write(f"Notes: {', '.join(note_names)}\n")
                f.write(f"MIDI: {', '.join(str(m) for m in midi_notes)}\n")
                f.write(f"Intervals: {', '.join(str(i) for i in intervals)}\n")

            # Generate MIDI
            midi_path = os.path.join(chord_dir, "chord.mid")
            generate_chord_midi(midi_notes, midi_path)

            # Render to WAV
            wav_path = os.path.join(chord_dir, "audio.wav")
            mp3_path = os.path.join(chord_dir, "audio.mp3")
            midi_to_wav(midi_path, wav_path)

            # Convert to MP3
            if wav_to_mp3(wav_path, mp3_path):
                os.remove(wav_path)
                ext = "mp3"
            else:
                ext = "wav"

            print(f"  {folder_name} ({', '.join(note_names)}) -> audio.{ext}")
            count += 1

    print(f"\nDone! Generated {count} chord folders in {ASSETS_DIR}")

if __name__ == "__main__":
    main()
