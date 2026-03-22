# Piano Anki Card Generator

Generate Anki flashcards for learning piano — notes, chords, and music theory — with audio, keyboard diagrams, staff notation, and fingering charts.

## What You Get

| Deck | Cards | Description |
|---|---|---|
| **Piano::Notes** | 88 | Staff notation + audio → note name + keyboard position |
| **Piano::Chords** | 168 | Two card types: staff→name and name→fingering (84 chords × 2) |
| **Piano::Theory** | 152 | Q&A cards across 33 music theory topics with diagrams |
| **Total** | **408** | |

### Chord Types
Major, Minor, Diminished, Augmented, Dominant 7th, Major 7th, Minor 7th — for all 12 roots.

### Theory Topics
Fundamentals (musical alphabet, half/whole steps, chromatic scale, enharmonics) → Scales & Keys (major/minor formulas, key signatures, circle of fifths) → Intervals → Chord Construction (triads, 7ths, inversions) → Harmony (diatonic chords, Roman numerals, common progressions) → Reading Music (clefs, note durations, time signatures, rests).

## Prerequisites

### System Dependencies

```bash
# macOS
brew install fluidsynth ffmpeg lilypond

# Ubuntu/Debian
sudo apt install fluidsynth ffmpeg lilypond
```

### SoundFont

Download a GM SoundFont and place it in the project root as `FluidR3_GM.sf2`:

```bash
# Option 1: FluidR3 (recommended)
# Download from: https://member.keymusician.com/Member/FluidR3_GM/FluidR3_GM.htm
# Place as FluidR3_GM.sf2 in this directory

# Option 2: On Ubuntu, install fluid-soundfont-gm and symlink
sudo apt install fluid-soundfont-gm
ln -s /usr/share/sounds/sf2/FluidR3_GM.sf2 .
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

### Anki

1. Install [Anki](https://apps.ankiweb.net/)
2. Install the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on (Tools → Add-ons → Get Add-ons → code: `2055492159`)
3. Restart Anki and keep it running while creating cards

## Usage

### Step 1: Generate Assets

Run these scripts in order to generate all audio, images, and theory content:

```bash
# Generate note audio + MIDI (88 notes)
python3 generate_notes.py

# Generate keyboard diagram images for notes
python3 generate_keyboard_images.py

# Generate staff notation images for notes (requires LilyPond)
python3 generate_staff_images.py

# Generate chord audio + MIDI (84 chords)
python3 generate_chords.py

# Generate keyboard diagrams for chords
python3 generate_chord_images.py

# Generate staff notation for chords (requires LilyPond)
# (handled by generate_staff_images.py)

# Generate fingering diagrams for chords
python3 generate_fingerings.py

# Generate theory Q&A content and diagrams
python3 generate_theory.py
```

Or run them all at once:

```bash
python3 generate_notes.py && \
python3 generate_keyboard_images.py && \
python3 generate_staff_images.py && \
python3 generate_chords.py && \
python3 generate_chord_images.py && \
python3 generate_fingerings.py && \
python3 generate_theory.py
```

### Step 2: Create Anki Cards

With Anki open and AnkiConnect running:

```bash
# Create note cards (88 cards)
python3 create_note_cards.py

# Create chord cards (168 cards)
python3 create_chord_cards.py

# Create theory cards (152 cards)
python3 create_theory_cards.py
```

## Project Structure

```
├── generate_notes.py           # Audio + MIDI for 88 notes
├── generate_keyboard_images.py # Keyboard diagrams for notes
├── generate_staff_images.py    # LilyPond staff notation
├── generate_chords.py          # Audio + MIDI for 84 chords
├── generate_chord_images.py    # Keyboard diagrams for chords
├── generate_fingerings.py      # Fingering diagrams (RH + LH)
├── generate_theory.py          # Theory Q&A + visual assets
├── create_note_cards.py        # Push note cards to Anki
├── create_chord_cards.py       # Push chord cards to Anki
├── create_theory_cards.py      # Push theory cards to Anki
├── anki_commands.py            # AnkiConnect helper
├── requirements.txt
└── assets/                     # Generated (gitignored)
    ├── notes/{NoteName}/       # audio.mp3, keyboard.png, staff.png
    ├── chords/{Name_type}/     # audio.mp3, keyboard.png, staff.png, fingering_*.png
    └── theory/{topic}/         # qa.txt, *.png diagrams
```

## License

MIT
