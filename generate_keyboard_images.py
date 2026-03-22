#!/usr/bin/env python3
"""Generate keyboard diagram images with highlighted keys for all 88 piano notes."""

import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "notes")

NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Which notes in an octave are white keys
WHITE_NOTES = {0, 2, 4, 5, 7, 9, 11}  # C, D, E, F, G, A, B
BLACK_NOTES = {1, 3, 6, 8, 10}         # Db, Eb, Gb, Ab, Bb

# 88-key piano: A0 (21) to C8 (108)
# White keys: A0, B0, then C1..B7, C8 = 52 white keys total
FIRST_MIDI = 21  # A0
LAST_MIDI = 108   # C8

# Dimensions
WHITE_KEY_W = 24
WHITE_KEY_H = 120
BLACK_KEY_W = 16
BLACK_KEY_H = 75
IMG_PADDING = 10

# Colors
WHITE_KEY_COLOR = (255, 255, 255)
BLACK_KEY_COLOR = (30, 30, 30)
HIGHLIGHT_COLOR = (65, 135, 245)  # Blue highlight
OUTLINE_COLOR = (100, 100, 100)
BG_COLOR = (240, 240, 240)

def get_white_key_positions():
    """Return a dict mapping MIDI number -> (x position, index) for white keys."""
    positions = {}
    x = IMG_PADDING
    idx = 0
    for midi_num in range(FIRST_MIDI, LAST_MIDI + 1):
        note_in_octave = midi_num % 12
        if note_in_octave in WHITE_NOTES:
            positions[midi_num] = (x, idx)
            x += WHITE_KEY_W
            idx += 1
    return positions

def get_black_key_positions(white_positions):
    """Return dict mapping MIDI number -> x position for black keys.
    Black keys sit between their adjacent white keys."""
    positions = {}
    for midi_num in range(FIRST_MIDI, LAST_MIDI + 1):
        note_in_octave = midi_num % 12
        if note_in_octave in BLACK_NOTES:
            # Find the white key just below and above
            lower_white = midi_num - 1
            upper_white = midi_num + 1
            if lower_white in white_positions and upper_white in white_positions:
                lx = white_positions[lower_white][0]
                ux = white_positions[upper_white][0]
                # Center the black key between them
                center = (lx + WHITE_KEY_W + ux) // 2
                positions[midi_num] = center - BLACK_KEY_W // 2
            elif lower_white in white_positions:
                lx = white_positions[lower_white][0]
                positions[midi_num] = lx + WHITE_KEY_W - BLACK_KEY_W // 2
            elif upper_white in white_positions:
                ux = white_positions[upper_white][0]
                positions[midi_num] = ux - BLACK_KEY_W // 2
    return positions

def midi_to_note_name(midi_num):
    octave = (midi_num // 12) - 1
    note_index = midi_num % 12
    return f"{NOTE_NAMES[note_index]}{octave}"

def draw_keyboard(highlight_midis, output_path, label=None):
    """Draw an 88-key piano keyboard with specified MIDI notes highlighted."""
    white_positions = get_white_key_positions()
    black_positions = get_black_key_positions(white_positions)

    num_white = len(white_positions)
    img_w = num_white * WHITE_KEY_W + IMG_PADDING * 2
    img_h = WHITE_KEY_H + IMG_PADDING * 2 + (30 if label else 0)

    img = Image.new("RGB", (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    highlight_set = set(highlight_midis) if not isinstance(highlight_midis, set) else highlight_midis

    # Draw white keys
    for midi_num, (x, _) in white_positions.items():
        y = IMG_PADDING
        color = HIGHLIGHT_COLOR if midi_num in highlight_set else WHITE_KEY_COLOR
        draw.rectangle([x, y, x + WHITE_KEY_W - 1, y + WHITE_KEY_H - 1], fill=color, outline=OUTLINE_COLOR)

    # Draw black keys on top
    for midi_num, x in black_positions.items():
        y = IMG_PADDING
        color = HIGHLIGHT_COLOR if midi_num in highlight_set else BLACK_KEY_COLOR
        draw.rectangle([x, y, x + BLACK_KEY_W - 1, y + BLACK_KEY_H - 1], fill=color, outline=OUTLINE_COLOR)

    # Add label
    if label:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except (OSError, IOError):
            font = ImageFont.load_default()
        text_y = IMG_PADDING + WHITE_KEY_H + 5
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_x = (img_w - text_w) // 2
        draw.text((text_x, text_y), label, fill=(30, 30, 30), font=font)

    img.save(output_path)

def main():
    for midi_num in range(FIRST_MIDI, LAST_MIDI + 1):
        note_name = midi_to_note_name(midi_num)
        note_dir = os.path.join(ASSETS_DIR, note_name)
        os.makedirs(note_dir, exist_ok=True)
        output_path = os.path.join(note_dir, "keyboard.png")
        draw_keyboard({midi_num}, output_path, label=note_name)
        print(f"  {note_name} -> keyboard.png")

    print(f"\nDone! Generated keyboard images for all 88 notes.")

if __name__ == "__main__":
    main()
