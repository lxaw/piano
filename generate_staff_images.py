#!/usr/bin/env python3
"""Generate grand staff notation images using LilyPond for professional engraving."""

import os
import subprocess
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# LilyPond pitch names: note letter + optional accidental
# LilyPond uses: cis = C#, ces = Cb, des = Db (dutch naming)
# Octave: c' = C4 (middle C), c'' = C5, c = C3, c, = C2, c,, = C1
MIDI_TO_LILYPOND = {}

LILY_NOTE_NAMES = {
    "C": "c", "Db": "des", "D": "d", "Eb": "ees",
    "E": "e", "F": "f", "Gb": "ges", "G": "g",
    "Ab": "aes", "A": "a", "Bb": "bes", "B": "b",
}

def midi_to_lily(midi_num):
    """Convert MIDI number to LilyPond pitch string."""
    note_index = midi_num % 12
    octave = (midi_num // 12) - 1
    name = NOTE_NAMES[note_index]
    lily_name = LILY_NOTE_NAMES[name]

    # LilyPond octave: c' = C4, c'' = C5, c = C3, c, = C2, c,, = C1
    if octave >= 4:
        lily_name += "'" * (octave - 3)
    elif octave < 3:
        lily_name += "," * (3 - octave)
    # octave 3 = no modifier (middle octave in LilyPond)

    return lily_name


def midi_to_note_name(midi_num):
    """Convert MIDI number to display name like C4."""
    note_index = midi_num % 12
    octave = (midi_num // 12) - 1
    return f"{NOTE_NAMES[note_index]}{octave}"


def generate_lilypond_source(midi_notes, title=None):
    """Generate LilyPond source for a grand staff with given notes."""
    # Determine which notes go on treble vs bass clef
    # Middle C (MIDI 60) and above -> treble, below -> bass
    treble_notes = [m for m in midi_notes if m >= 60]
    bass_notes = [m for m in midi_notes if m < 60]

    # Build note expressions
    if treble_notes:
        if len(treble_notes) == 1:
            treble_expr = f"{midi_to_lily(treble_notes[0])}1"
        else:
            chord = " ".join(midi_to_lily(m) for m in sorted(treble_notes))
            treble_expr = f"<{chord}>1"
    else:
        treble_expr = "s1"  # invisible rest

    if bass_notes:
        if len(bass_notes) == 1:
            bass_expr = f"{midi_to_lily(bass_notes[0])}1"
        else:
            chord = " ".join(midi_to_lily(m) for m in sorted(bass_notes))
            bass_expr = f"<{chord}>1"
    else:
        bass_expr = "s1"

    lily_source = f"""\\version "2.24.0"

\\header {{
  tagline = ""
}}

\\paper {{
  indent = 0
  paper-width = 45\\mm
  paper-height = 45\\mm
  top-margin = 3\\mm
  bottom-margin = 2\\mm
  left-margin = 3\\mm
  right-margin = 3\\mm
  ragged-right = ##t
}}

\\score {{
  \\new PianoStaff <<
    \\new Staff {{
      \\clef treble
      \\override Staff.TimeSignature.stencil = ##f
      \\override Staff.BarLine.stencil = ##f
      {treble_expr}
    }}
    \\new Staff {{
      \\clef bass
      \\override Staff.TimeSignature.stencil = ##f
      \\override Staff.BarLine.stencil = ##f
      {bass_expr}
    }}
  >>
  \\layout {{ }}
}}
"""
    return lily_source


def render_lilypond(lily_source, output_png_path):
    """Render LilyPond source to a cropped PNG."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ly_path = os.path.join(tmpdir, "score.ly")
        with open(ly_path, "w") as f:
            f.write(lily_source)

        # Run lilypond to produce PNG
        result = subprocess.run([
            "lilypond", "-dbackend=eps", "-dno-gs-load-fonts",
            "-dinclude-eps-fonts", "--png", "-dresolution=200",
            "-o", os.path.join(tmpdir, "score"),
            ly_path
        ], capture_output=True, text=True, cwd=tmpdir)

        if result.returncode != 0:
            print(f"  LilyPond error: {result.stderr[:200]}")
            return False

        # LilyPond outputs score.png
        rendered = os.path.join(tmpdir, "score.png")
        if not os.path.exists(rendered):
            print(f"  No PNG output found")
            return False

        # Crop whitespace using Pillow
        from PIL import Image
        img = Image.open(rendered)
        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Find bounding box of non-white content
        bbox = img.getbbox()
        if bbox:
            # Add a small padding
            pad = 15
            bbox = (
                max(0, bbox[0] - pad),
                max(0, bbox[1] - pad),
                min(img.width, bbox[2] + pad),
                min(img.height, bbox[3] + pad),
            )
            img = img.crop(bbox)

        img.save(output_png_path)
        return True


def generate_note_staves():
    """Generate staff images for all 88 individual notes."""
    notes_dir = os.path.join(BASE_DIR, "assets", "notes")
    for midi_num in range(21, 109):  # A0 to C8
        note_name = midi_to_note_name(midi_num)
        note_dir = os.path.join(notes_dir, note_name)
        os.makedirs(note_dir, exist_ok=True)
        output = os.path.join(note_dir, "staff.png")

        lily = generate_lilypond_source([midi_num])
        if render_lilypond(lily, output):
            print(f"  {note_name} -> staff.png")
        else:
            print(f"  {note_name} FAILED")


def generate_chord_staves():
    """Generate staff images for all chords."""
    chords_dir = os.path.join(BASE_DIR, "assets", "chords")
    CHORD_TYPES = {
        "major":      [0, 4, 7],
        "minor":      [0, 3, 7],
        "diminished": [0, 3, 6],
        "augmented":  [0, 4, 8],
        "dominant7":  [0, 4, 7, 10],
        "major7":     [0, 4, 7, 11],
        "minor7":     [0, 3, 7, 10],
    }
    BASE_OCTAVE_MIDI = 60

    for root_idx, root_name in enumerate(NOTE_NAMES):
        for chord_type, intervals in CHORD_TYPES.items():
            folder_name = f"{root_name}_{chord_type}"
            chord_dir = os.path.join(chords_dir, folder_name)
            root_midi = BASE_OCTAVE_MIDI + root_idx
            midi_notes = [root_midi + iv for iv in intervals]
            output = os.path.join(chord_dir, "staff.png")

            lily = generate_lilypond_source(midi_notes)
            if render_lilypond(lily, output):
                print(f"  {folder_name} -> staff.png")
            else:
                print(f"  {folder_name} FAILED")


if __name__ == "__main__":
    print("Generating note staff images with LilyPond...")
    generate_note_staves()
    print("\nGenerating chord staff images with LilyPond...")
    generate_chord_staves()
