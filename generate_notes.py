#!/usr/bin/env python3
"""Generate folders with MIDI and audio files for all 88 piano keys."""

import os
import subprocess
from midiutil import MIDIFile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "notes")
SOUNDFONT = os.path.join(BASE_DIR, "FluidR3_GM.sf2")

# Standard 88-key piano: A0 (MIDI 21) through C8 (MIDI 108)
NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

def midi_to_note_name(midi_num):
    """Convert MIDI number to note name like C4, Db3, etc."""
    octave = (midi_num // 12) - 1
    note_index = midi_num % 12
    return f"{NOTE_NAMES[note_index]}{octave}"

def generate_midi(midi_num, output_path):
    """Generate a MIDI file for a single note."""
    midi = MIDIFile(1)
    midi.addTempo(0, 0, 120)
    midi.addProgramChange(0, 0, 0, 0)  # Acoustic Grand Piano
    midi.addNote(0, 0, midi_num, 0, 2, 100)  # 2 beats duration, velocity 100
    with open(output_path, "wb") as f:
        midi.writeFile(f)

def midi_to_wav(midi_path, wav_path):
    """Render MIDI to WAV using fluidsynth."""
    subprocess.run([
        "fluidsynth", "-ni", "-F", wav_path, "-r", "44100",
        SOUNDFONT, midi_path
    ], check=True, capture_output=True)

def wav_to_mp3(wav_path, mp3_path):
    """Convert WAV to MP3 using ffmpeg or lame. Falls back to keeping WAV."""
    # Try ffmpeg first
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path, "-b:a", "192k", mp3_path
        ], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    # Try lame
    try:
        subprocess.run([
            "lame", "--preset", "standard", wav_path, mp3_path
        ], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # Check for mp3 conversion capability
    has_mp3 = False
    for tool in ["ffmpeg", "lame"]:
        try:
            subprocess.run([tool, "--version"], capture_output=True)
            has_mp3 = True
            break
        except FileNotFoundError:
            continue

    if not has_mp3:
        print("WARNING: No ffmpeg or lame found. Audio will be WAV format.")
        print("Install ffmpeg for MP3: brew install ffmpeg")

    for midi_num in range(21, 109):  # A0=21 to C8=108
        note_name = midi_to_note_name(midi_num)
        note_dir = os.path.join(ASSETS_DIR, note_name)
        os.makedirs(note_dir, exist_ok=True)

        midi_path = os.path.join(note_dir, "note.mid")
        wav_path = os.path.join(note_dir, "audio.wav")
        mp3_path = os.path.join(note_dir, "audio.mp3")

        # Generate MIDI
        generate_midi(midi_num, midi_path)

        # Render to WAV
        midi_to_wav(midi_path, wav_path)

        # Convert to MP3 if possible
        if has_mp3:
            if wav_to_mp3(wav_path, mp3_path):
                os.remove(wav_path)  # Clean up WAV
                audio_ext = "mp3"
            else:
                audio_ext = "wav"
        else:
            audio_ext = "wav"

        print(f"  {note_name} (MIDI {midi_num}) -> audio.{audio_ext}")

    print(f"\nDone! Generated {108 - 21 + 1} note folders in {ASSETS_DIR}")

if __name__ == "__main__":
    main()
