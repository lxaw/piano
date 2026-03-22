#!/usr/bin/env python3
"""Generate fingering data and keyboard images with finger numbers for all chords."""

import os
from PIL import Image, ImageDraw, ImageFont
from generate_keyboard_images import (
    get_white_key_positions, get_black_key_positions,
    WHITE_NOTES, BLACK_NOTES, FIRST_MIDI, LAST_MIDI,
    WHITE_KEY_W, WHITE_KEY_H, BLACK_KEY_W, BLACK_KEY_H,
    IMG_PADDING, WHITE_KEY_COLOR, BLACK_KEY_COLOR,
    HIGHLIGHT_COLOR, OUTLINE_COLOR, BG_COLOR,
)

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

CHORD_DISPLAY = {
    "major": "Major", "minor": "Minor", "diminished": "Dim",
    "augmented": "Aug", "dominant7": "Dom7", "major7": "Maj7", "minor7": "Min7",
}

BASE_OCTAVE_MIDI = 60  # C4


def get_fingering(intervals):
    """Return (right_hand, left_hand) fingering tuples for a chord.

    Standard root-position fingerings:
      Triads (3 notes): RH 1-3-5, LH 5-3-1
      7th chords (4 notes): RH 1-2-3-5, LH 5-3-2-1
    """
    if len(intervals) == 3:
        return (1, 3, 5), (5, 3, 1)
    elif len(intervals) == 4:
        return (1, 2, 3, 5), (5, 3, 2, 1)
    else:
        # Fallback for any other size
        return tuple(range(1, len(intervals) + 1)), tuple(range(len(intervals), 0, -1))


def get_font(size):
    for path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def draw_keyboard_with_fingering(midi_notes, fingering, output_path, label=None):
    """Draw a zoomed-in keyboard section with finger numbers on highlighted keys.

    midi_notes: list of MIDI numbers (sorted low to high)
    fingering: tuple of finger numbers matching midi_notes order
    """
    white_positions = get_white_key_positions()
    black_positions = get_black_key_positions(white_positions)

    # Find the range of keys to show (zoom into the relevant octaves)
    min_midi = min(midi_notes)
    max_midi = max(midi_notes)

    # Show ~1.5 octaves around the chord for context
    view_start = max(FIRST_MIDI, min_midi - 7)
    view_end = min(LAST_MIDI, max_midi + 7)

    # Snap to white key boundaries
    while view_start % 12 not in {0, 5, 9} and view_start > FIRST_MIDI:
        view_start -= 1
    while view_end % 12 not in {4, 11} and view_end < LAST_MIDI:
        view_end += 1

    # Get visible white keys for sizing
    visible_white = {m: pos for m, pos in white_positions.items()
                     if view_start <= m <= view_end}
    if not visible_white:
        return

    # Calculate offset so visible keys start at left
    min_white_x = min(pos[0] for pos in visible_white.values())
    x_offset = IMG_PADDING - min_white_x

    num_visible_white = len(visible_white)
    label_h = 55 if label else 0
    img_w = num_visible_white * WHITE_KEY_W + IMG_PADDING * 2
    img_h = WHITE_KEY_H + IMG_PADDING * 2 + label_h

    img = Image.new("RGB", (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    highlight_set = set(midi_notes)
    finger_map = dict(zip(midi_notes, fingering))

    font_finger = get_font(14)
    font_label = get_font(14)

    # Draw white keys
    for midi_num in range(view_start, view_end + 1):
        if midi_num not in white_positions:
            continue
        note_in_octave = midi_num % 12
        if note_in_octave not in WHITE_NOTES:
            continue

        orig_x = white_positions[midi_num][0]
        x = orig_x + x_offset
        y = IMG_PADDING

        is_highlighted = midi_num in highlight_set
        color = HIGHLIGHT_COLOR if is_highlighted else WHITE_KEY_COLOR
        draw.rectangle([x, y, x + WHITE_KEY_W - 1, y + WHITE_KEY_H - 1],
                       fill=color, outline=OUTLINE_COLOR)

        # Draw finger number on white key
        if is_highlighted and midi_num in finger_map:
            finger = str(finger_map[midi_num])
            bbox = draw.textbbox((0, 0), finger, font=font_finger)
            fw = bbox[2] - bbox[0]
            fh = bbox[3] - bbox[1]
            fx = x + (WHITE_KEY_W - fw) // 2
            fy = y + WHITE_KEY_H - fh - 10
            # Draw circle behind number
            cr = 11
            cx = fx + fw // 2
            cy = fy + fh // 2
            draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                         fill=(255, 255, 255), outline=(50, 50, 50), width=2)
            draw.text((fx, fy), finger, fill=(30, 30, 30), font=font_finger)

    # Draw black keys
    for midi_num in range(view_start, view_end + 1):
        if midi_num not in black_positions:
            continue

        orig_x = black_positions[midi_num]
        x = orig_x + x_offset
        y = IMG_PADDING

        is_highlighted = midi_num in highlight_set
        color = HIGHLIGHT_COLOR if is_highlighted else BLACK_KEY_COLOR
        draw.rectangle([x, y, x + BLACK_KEY_W - 1, y + BLACK_KEY_H - 1],
                       fill=color, outline=OUTLINE_COLOR)

        # Draw finger number on black key
        if is_highlighted and midi_num in finger_map:
            finger = str(finger_map[midi_num])
            bbox = draw.textbbox((0, 0), finger, font=font_finger)
            fw = bbox[2] - bbox[0]
            fh = bbox[3] - bbox[1]
            fx = x + (BLACK_KEY_W - fw) // 2
            fy = y + BLACK_KEY_H - fh - 8
            cr = 10
            cx = fx + fw // 2
            cy = fy + fh // 2
            draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                         fill=(255, 255, 255), outline=(50, 50, 50), width=2)
            draw.text((fx, fy), finger, fill=(30, 30, 30), font=font_finger)

    # Add label below keyboard
    if label:
        text_y = IMG_PADDING + WHITE_KEY_H + 8
        bbox = draw.textbbox((0, 0), label, font=font_label)
        text_w = bbox[2] - bbox[0]
        text_x = (img_w - text_w) // 2
        draw.text((text_x, text_y), label, fill=(30, 30, 30), font=font_label)

    img.save(output_path)


def format_fingering(notes, fingering):
    """Format fingering as readable string like '1(C4) - 3(E4) - 5(G4)'."""
    parts = []
    for midi_num, finger in zip(notes, fingering):
        note_idx = midi_num % 12
        octave = (midi_num // 12) - 1
        name = NOTE_NAMES[note_idx]
        parts.append(f"{finger}({name}{octave})")
    return " - ".join(parts)


def main():
    count = 0
    for root_idx, root_name in enumerate(NOTE_NAMES):
        for chord_type, intervals in CHORD_TYPES.items():
            folder_name = f"{root_name}_{chord_type}"
            chord_dir = os.path.join(CHORDS_DIR, folder_name)
            os.makedirs(chord_dir, exist_ok=True)

            root_midi = BASE_OCTAVE_MIDI + root_idx
            midi_notes = sorted([root_midi + iv for iv in intervals])
            rh_fingers, lh_fingers = get_fingering(intervals)

            display = f"{root_name} {CHORD_DISPLAY[chord_type]}"

            # Generate RH image
            rh_label = f"{display} — RH: {'-'.join(str(f) for f in rh_fingers)}"
            draw_keyboard_with_fingering(
                midi_notes, rh_fingers,
                os.path.join(chord_dir, "fingering_rh.png"),
                label=rh_label
            )

            # Generate LH image (same notes, one octave lower for left hand)
            lh_midi_notes = sorted([m - 12 for m in midi_notes])
            lh_label = f"{display} — LH: {'-'.join(str(f) for f in lh_fingers)}"
            draw_keyboard_with_fingering(
                lh_midi_notes, lh_fingers,
                os.path.join(chord_dir, "fingering_lh.png"),
                label=lh_label
            )

            # Update info.txt with fingering data
            info_path = os.path.join(chord_dir, "info.txt")
            existing = ""
            if os.path.exists(info_path):
                with open(info_path, "r") as f:
                    existing = f.read()

            # Remove old fingering lines if regenerating
            lines = [l for l in existing.strip().split("\n")
                     if not l.startswith("RH Fingering:") and
                        not l.startswith("LH Fingering:") and
                        not l.startswith("RH Notes:") and
                        not l.startswith("LH Notes:")]

            lines.append(f"RH Fingering: {'-'.join(str(f) for f in rh_fingers)}")
            lines.append(f"RH Notes: {format_fingering(midi_notes, rh_fingers)}")
            lines.append(f"LH Fingering: {'-'.join(str(f) for f in lh_fingers)}")
            lines.append(f"LH Notes: {format_fingering(lh_midi_notes, lh_fingers)}")

            with open(info_path, "w") as f:
                f.write("\n".join(lines) + "\n")

            print(f"  {folder_name} -> fingering_rh.png, fingering_lh.png, info.txt")
            count += 1

    print(f"\nDone! Generated fingering assets for {count} chords.")


if __name__ == "__main__":
    main()
