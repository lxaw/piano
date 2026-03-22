#!/usr/bin/env python3
"""Generate theory topic folders with Q&A files and visual assets for piano Anki cards."""

import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_keyboard_images import (
    draw_keyboard, get_white_key_positions, get_black_key_positions,
    WHITE_NOTES, BLACK_NOTES, FIRST_MIDI, LAST_MIDI,
    WHITE_KEY_W, WHITE_KEY_H, BLACK_KEY_W, BLACK_KEY_H,
    IMG_PADDING, WHITE_KEY_COLOR, BLACK_KEY_COLOR,
    HIGHLIGHT_COLOR, OUTLINE_COLOR, BG_COLOR,
)
from generate_staff_images import generate_lilypond_source, render_lilypond, midi_to_lily

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THEORY_DIR = os.path.join(BASE_DIR, "assets", "theory")

NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
NOTE_NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


# ─── Fonts ───────────────────────────────────────────────────────────────────

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


def get_bold_font(size):
    for path in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return get_font(size)


# ─── Keyboard diagram helpers ────────────────────────────────────────────────

def draw_zoomed_keyboard(highlight_midis, output_path, label=None,
                         annotations=None, show_labels=False,
                         center_midi=None, span_semitones=24):
    """Draw a zoomed keyboard section with optional annotations on keys.

    annotations: dict of {midi_num: text_to_draw_on_key}
    show_labels: if True, label every white key with its note name
    """
    white_positions = get_white_key_positions()
    black_positions = get_black_key_positions(white_positions)

    if center_midi is None:
        if highlight_midis:
            center_midi = (min(highlight_midis) + max(highlight_midis)) // 2
        else:
            center_midi = 60

    view_start = max(FIRST_MIDI, center_midi - span_semitones // 2)
    view_end = min(LAST_MIDI, center_midi + span_semitones // 2)

    # Snap to C boundaries for clean display
    while view_start % 12 != 0 and view_start > FIRST_MIDI:
        view_start -= 1
    while view_end % 12 != 11 and view_end < LAST_MIDI:
        view_end += 1

    visible_white = {m: pos for m, pos in white_positions.items()
                     if view_start <= m <= view_end}
    if not visible_white:
        return

    min_white_x = min(pos[0] for pos in visible_white.values())
    x_offset = IMG_PADDING - min_white_x

    num_visible_white = len(visible_white)
    label_h = 30 if label else 0
    note_label_h = 25 if show_labels else 0
    img_w = num_visible_white * WHITE_KEY_W + IMG_PADDING * 2
    img_h = WHITE_KEY_H + IMG_PADDING * 2 + label_h + note_label_h

    img = Image.new("RGB", (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    highlight_set = set(highlight_midis) if highlight_midis else set()
    annotations = annotations or {}

    font_small = get_font(10)
    font_annot = get_font(12)
    font_label = get_font(14)

    # Draw white keys
    for midi_num in range(view_start, view_end + 1):
        if midi_num not in white_positions:
            continue
        if midi_num % 12 not in WHITE_NOTES:
            continue

        orig_x = white_positions[midi_num][0]
        x = orig_x + x_offset
        y = IMG_PADDING

        is_hl = midi_num in highlight_set
        color = HIGHLIGHT_COLOR if is_hl else WHITE_KEY_COLOR
        draw.rectangle([x, y, x + WHITE_KEY_W - 1, y + WHITE_KEY_H - 1],
                       fill=color, outline=OUTLINE_COLOR)

        # Annotation on key
        if midi_num in annotations:
            txt = annotations[midi_num]
            bbox = draw.textbbox((0, 0), txt, font=font_annot)
            tw = bbox[2] - bbox[0]
            tx = x + (WHITE_KEY_W - tw) // 2
            ty = y + WHITE_KEY_H - 22
            text_color = (255, 255, 255) if is_hl else (80, 80, 80)
            draw.text((tx, ty), txt, fill=text_color, font=font_annot)

        # Note name below key
        if show_labels:
            note_idx = midi_num % 12
            octave = (midi_num // 12) - 1
            name = NOTE_NAMES[note_idx]
            lbl = f"{name}{octave}"
            bbox = draw.textbbox((0, 0), lbl, font=font_small)
            tw = bbox[2] - bbox[0]
            tx = x + (WHITE_KEY_W - tw) // 2
            ty = y + WHITE_KEY_H + 3
            draw.text((tx, ty), lbl, fill=(80, 80, 80), font=font_small)

    # Draw black keys
    for midi_num in range(view_start, view_end + 1):
        if midi_num not in black_positions:
            continue

        orig_x = black_positions[midi_num]
        x = orig_x + x_offset
        y = IMG_PADDING

        is_hl = midi_num in highlight_set
        color = HIGHLIGHT_COLOR if is_hl else BLACK_KEY_COLOR
        draw.rectangle([x, y, x + BLACK_KEY_W - 1, y + BLACK_KEY_H - 1],
                       fill=color, outline=OUTLINE_COLOR)

        if midi_num in annotations:
            txt = annotations[midi_num]
            bbox = draw.textbbox((0, 0), txt, font=font_small)
            tw = bbox[2] - bbox[0]
            tx = x + (BLACK_KEY_W - tw) // 2
            ty = y + BLACK_KEY_H - 18
            draw.text((tx, ty), txt, fill=(255, 255, 255), font=font_small)

        if show_labels:
            note_idx = midi_num % 12
            octave = (midi_num // 12) - 1
            name = NOTE_NAMES[note_idx]
            lbl = f"{name}{octave}"
            bbox = draw.textbbox((0, 0), lbl, font=font_small)
            tw = bbox[2] - bbox[0]
            # Place above key area, angled position
            tx = x + (BLACK_KEY_W - tw) // 2
            ty = y + BLACK_KEY_H + 3
            draw.text((tx, ty), lbl, fill=(80, 80, 80), font=font_small)

    # Title label
    if label:
        text_y = img_h - label_h + 2
        bbox = draw.textbbox((0, 0), label, font=font_label)
        text_w = bbox[2] - bbox[0]
        text_x = (img_w - text_w) // 2
        draw.text((text_x, text_y), label, fill=(30, 30, 30), font=font_label)

    img.save(output_path)


def draw_step_diagram(output_path, steps, start_midi=60, label=None):
    """Draw a keyboard with W (whole) and H (half) step brackets between notes.

    steps: list of ('W' or 'H', midi_from, midi_to)
    """
    all_midis = set()
    for _, m1, m2 in steps:
        all_midis.add(m1)
        all_midis.add(m2)

    white_positions = get_white_key_positions()
    black_positions = get_black_key_positions(white_positions)

    view_start = max(FIRST_MIDI, min(all_midis) - 2)
    view_end = min(LAST_MIDI, max(all_midis) + 2)
    while view_start % 12 != 0 and view_start > FIRST_MIDI:
        view_start -= 1
    while view_end % 12 != 11 and view_end < LAST_MIDI:
        view_end += 1

    visible_white = {m: pos for m, pos in white_positions.items()
                     if view_start <= m <= view_end}
    if not visible_white:
        return

    min_white_x = min(pos[0] for pos in visible_white.values())
    x_offset = IMG_PADDING - min_white_x

    num_visible_white = len(visible_white)
    bracket_h = 45
    label_h = 30 if label else 0
    img_w = num_visible_white * WHITE_KEY_W + IMG_PADDING * 2
    img_h = WHITE_KEY_H + IMG_PADDING * 2 + bracket_h + label_h

    img = Image.new("RGB", (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_step = get_font(13)
    font_note = get_font(11)
    font_label = get_font(14)

    # Draw white keys
    for midi_num in range(view_start, view_end + 1):
        if midi_num not in white_positions or midi_num % 12 not in WHITE_NOTES:
            continue
        orig_x = white_positions[midi_num][0]
        x = orig_x + x_offset
        y = IMG_PADDING
        is_hl = midi_num in all_midis
        color = HIGHLIGHT_COLOR if is_hl else WHITE_KEY_COLOR
        draw.rectangle([x, y, x + WHITE_KEY_W - 1, y + WHITE_KEY_H - 1],
                       fill=color, outline=OUTLINE_COLOR)
        if is_hl:
            note_idx = midi_num % 12
            name = NOTE_NAMES[note_idx]
            bbox = draw.textbbox((0, 0), name, font=font_note)
            tw = bbox[2] - bbox[0]
            tx = x + (WHITE_KEY_W - tw) // 2
            ty = y + WHITE_KEY_H - 20
            draw.text((tx, ty), name, fill=(255, 255, 255), font=font_note)

    # Draw black keys
    for midi_num in range(view_start, view_end + 1):
        if midi_num not in black_positions:
            continue
        orig_x = black_positions[midi_num]
        x = orig_x + x_offset
        y = IMG_PADDING
        is_hl = midi_num in all_midis
        color = HIGHLIGHT_COLOR if is_hl else BLACK_KEY_COLOR
        draw.rectangle([x, y, x + BLACK_KEY_W - 1, y + BLACK_KEY_H - 1],
                       fill=color, outline=OUTLINE_COLOR)
        if is_hl:
            note_idx = midi_num % 12
            name = NOTE_NAMES[note_idx]
            bbox = draw.textbbox((0, 0), name, font=font_note)
            tw = bbox[2] - bbox[0]
            tx = x + (BLACK_KEY_W - tw) // 2
            ty = y + BLACK_KEY_H - 18
            draw.text((tx, ty), name, fill=(255, 255, 255), font=font_note)

    # Draw step brackets below keyboard
    bracket_y_start = IMG_PADDING + WHITE_KEY_H + 5

    def get_key_center_x(midi_num):
        if midi_num in white_positions:
            return white_positions[midi_num][0] + x_offset + WHITE_KEY_W // 2
        elif midi_num in black_positions:
            return black_positions[midi_num] + x_offset + BLACK_KEY_W // 2
        return 0

    colors_step = {"W": (0, 130, 70), "H": (200, 50, 50)}

    for i, (step_type, m1, m2) in enumerate(steps):
        x1 = get_key_center_x(m1)
        x2 = get_key_center_x(m2)
        row = i % 2  # Stagger rows to avoid overlap
        by = bracket_y_start + row * 20
        color = colors_step.get(step_type, (100, 100, 100))

        # Draw bracket
        draw.line([(x1, by), (x1, by + 10), (x2, by + 10), (x2, by)],
                  fill=color, width=2)
        # Label
        bbox = draw.textbbox((0, 0), step_type, font=font_step)
        tw = bbox[2] - bbox[0]
        tx = (x1 + x2) // 2 - tw // 2
        ty = by + 11
        draw.text((tx, ty), step_type, fill=color, font=font_step)

    if label:
        text_y = img_h - label_h + 2
        bbox = draw.textbbox((0, 0), label, font=font_label)
        tw = bbox[2] - bbox[0]
        tx = (img_w - tw) // 2
        draw.text((tx, text_y), label, fill=(30, 30, 30), font=font_label)

    img.save(output_path)


# ─── Circle of Fifths ────────────────────────────────────────────────────────

def draw_circle_of_fifths(output_path):
    """Draw a circle of fifths diagram."""
    size = 600
    center = size // 2
    img = Image.new("RGB", (size, size + 40), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_major = get_bold_font(18)
    font_minor = get_font(14)
    font_title = get_bold_font(16)

    # Major keys (outer ring) — order of fifths starting at top (C)
    major_keys = ["C", "G", "D", "A", "E", "B/Cb", "Gb/F#", "Db", "Ab", "Eb", "Bb", "F"]
    # Relative minor keys (inner ring)
    minor_keys = ["Am", "Em", "Bm", "F#m", "C#m", "G#m/Abm", "Ebm/D#m", "Bbm", "Fm", "Cm", "Gm", "Dm"]
    # Number of sharps/flats
    sig_labels = ["0", "1#", "2#", "3#", "4#", "5#/7b", "6b/6#", "5b", "4b", "3b", "2b", "1b"]

    outer_r = 230
    inner_r = 160
    sig_r = 195

    # Draw circles
    draw.ellipse([center - outer_r - 20, center - outer_r - 20,
                  center + outer_r + 20, center + outer_r + 20],
                 outline=(180, 180, 180), width=2)
    draw.ellipse([center - inner_r + 10, center - inner_r + 10,
                  center + inner_r - 10, center + inner_r - 10],
                 outline=(200, 200, 200), width=1)

    for i in range(12):
        angle = math.radians(-90 + i * 30)  # Start at top (12 o'clock)

        # Major key (outer)
        mx = center + int(outer_r * math.cos(angle))
        my = center + int(outer_r * math.sin(angle))
        txt = major_keys[i]
        bbox = draw.textbbox((0, 0), txt, font=font_major)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((mx - tw // 2, my - th // 2), txt, fill=(30, 30, 30), font=font_major)

        # Key signature (middle ring)
        sx = center + int(sig_r * math.cos(angle))
        sy = center + int(sig_r * math.sin(angle))
        sig = sig_labels[i]
        bbox = draw.textbbox((0, 0), sig, font=font_minor)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((sx - tw // 2, sy - th // 2), sig, fill=(130, 130, 130), font=font_minor)

        # Minor key (inner)
        ix = center + int(inner_r * math.cos(angle))
        iy = center + int(inner_r * math.sin(angle))
        txt = minor_keys[i]
        bbox = draw.textbbox((0, 0), txt, font=font_minor)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((ix - tw // 2, iy - th // 2), txt, fill=(65, 135, 245), font=font_minor)

        # Draw spoke lines
        lx1 = center + int((inner_r - 25) * math.cos(angle + math.radians(15)))
        ly1 = center + int((inner_r - 25) * math.sin(angle + math.radians(15)))
        lx2 = center + int((outer_r + 15) * math.cos(angle + math.radians(15)))
        ly2 = center + int((outer_r + 15) * math.sin(angle + math.radians(15)))
        draw.line([(lx1, ly1), (lx2, ly2)], fill=(220, 220, 220), width=1)

    # Title
    title = "Circle of Fifths"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((size - tw) // 2, size + 10), title, fill=(30, 30, 30), font=font_title)

    # Legend
    legend_font = get_font(12)
    draw.text((10, size + 10), "Outer: Major keys", fill=(30, 30, 30), font=legend_font)
    draw.text((10, size + 24), "Inner: Minor keys", fill=(65, 135, 245), font=legend_font)

    img.save(output_path)


# ─── LilyPond helpers ────────────────────────────────────────────────────────

def render_lily_custom(lily_source, output_path):
    """Render arbitrary LilyPond source to PNG."""
    import tempfile
    import subprocess
    with tempfile.TemporaryDirectory() as tmpdir:
        ly_path = os.path.join(tmpdir, "score.ly")
        with open(ly_path, "w") as f:
            f.write(lily_source)

        result = subprocess.run([
            "lilypond", "-dbackend=eps", "-dno-gs-load-fonts",
            "-dinclude-eps-fonts", "--png", "-dresolution=200",
            "-o", os.path.join(tmpdir, "score"), ly_path
        ], capture_output=True, text=True, cwd=tmpdir)

        if result.returncode != 0:
            print(f"  LilyPond error: {result.stderr[:300]}")
            return False

        rendered = os.path.join(tmpdir, "score.png")
        if not os.path.exists(rendered):
            return False

        img = Image.open(rendered)
        if img.mode != "RGB":
            img = img.convert("RGB")
        bbox = img.getbbox()
        if bbox:
            pad = 15
            bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                    min(img.width, bbox[2] + pad), min(img.height, bbox[3] + pad))
            img = img.crop(bbox)
        img.save(output_path)
        return True


def lily_key_signature(key_name, mode="major"):
    """Generate LilyPond source for a key signature."""
    # Map key names to LilyPond key names
    key_map = {
        "C": "c", "G": "g", "D": "d", "A": "a", "E": "e", "B": "b",
        "F#": "fis", "Gb": "ges", "Db": "des", "Ab": "aes",
        "Eb": "ees", "Bb": "bes", "F": "f",
        "Cb": "ces", "C#": "cis",
    }
    lily_key = key_map.get(key_name, "c")
    lily_mode = "\\major" if mode == "major" else "\\minor"

    return f"""\\version "2.24.0"
\\header {{ tagline = "" }}
\\paper {{
  indent = 0
  paper-width = 50\\mm
  paper-height = 25\\mm
  top-margin = 2\\mm
  bottom-margin = 2\\mm
  left-margin = 3\\mm
  right-margin = 3\\mm
  ragged-right = ##t
}}
\\score {{
  \\new Staff {{
    \\clef treble
    \\key {lily_key} {lily_mode}
    \\override Staff.TimeSignature.stencil = ##f
    \\override Staff.BarLine.stencil = ##f
    s1
  }}
  \\layout {{ }}
}}
"""


def lily_note_durations():
    """Generate LilyPond source showing note duration types."""
    return """\\version "2.24.0"
\\header { tagline = "" }
\\paper {
  indent = 0
  paper-width = 120\\mm
  paper-height = 30\\mm
  top-margin = 2\\mm
  bottom-margin = 2\\mm
  left-margin = 3\\mm
  right-margin = 3\\mm
  ragged-right = ##t
}
\\score {
  \\new Staff {
    \\clef treble
    \\override Staff.TimeSignature.stencil = ##f
    \\override Staff.BarLine.stencil = ##f
    c'1^"Whole"
    c'2^"Half" c'2
    c'4^"Quarter" c'4 c'4 c'4
    c'8^"Eighth" c'8 c'8 c'8 c'8 c'8 c'8 c'8
    c'16^"16th" c'16 c'16 c'16 c'16 c'16 c'16 c'16
    c'16 c'16 c'16 c'16 c'16 c'16 c'16 c'16
  }
  \\layout { }
}
"""


def lily_rests():
    """Generate LilyPond source showing rest types."""
    return """\\version "2.24.0"
\\header { tagline = "" }
\\paper {
  indent = 0
  paper-width = 100\\mm
  paper-height = 30\\mm
  top-margin = 2\\mm
  bottom-margin = 2\\mm
  left-margin = 3\\mm
  right-margin = 3\\mm
  ragged-right = ##t
}
\\score {
  \\new Staff {
    \\clef treble
    \\override Staff.TimeSignature.stencil = ##f
    \\override Staff.BarLine.stencil = ##f
    r1^"Whole rest"
    r2^"Half rest" r2
    r4^"Quarter" r4 r4 r4
    r8^"Eighth" r8 r8 r8 r8 r8 r8 r8
    r16^"16th" r16 r16 r16 r16 r16 r16 r16
    r16 r16 r16 r16 r16 r16 r16 r16
  }
  \\layout { }
}
"""


def lily_time_signatures():
    """Generate LilyPond showing common time signatures."""
    return """\\version "2.24.0"
\\header { tagline = "" }
\\paper {
  indent = 0
  paper-width = 130\\mm
  paper-height = 30\\mm
  top-margin = 2\\mm
  bottom-margin = 2\\mm
  left-margin = 3\\mm
  right-margin = 3\\mm
  ragged-right = ##t
}
\\score {
  \\new Staff {
    \\override Staff.BarLine.stencil = ##f
    \\time 4/4 c'4^"4/4" c'4 c'4 c'4
    \\bar "||"
    \\time 3/4 c'4^"3/4" c'4 c'4
    \\bar "||"
    \\time 2/4 c'4^"2/4" c'4
    \\bar "||"
    \\time 6/8 c'8^"6/8" c'8 c'8 c'8 c'8 c'8
    \\bar "|."
  }
  \\layout { }
}
"""


def lily_treble_clef_notes():
    """LilyPond showing treble clef line and space note names."""
    return """\\version "2.24.0"
\\header { tagline = "" }
\\paper {
  indent = 0
  paper-width = 90\\mm
  paper-height = 40\\mm
  top-margin = 2\\mm
  bottom-margin = 2\\mm
  left-margin = 3\\mm
  right-margin = 3\\mm
  ragged-right = ##t
}
\\score {
  \\new Staff {
    \\clef treble
    \\override Staff.TimeSignature.stencil = ##f
    \\override Staff.BarLine.stencil = ##f
    e'1^"E"
    f'1^"F"
    g'1^"G"
    a'1^"A"
    b'1^"B"
    c''1^"C"
    d''1^"D"
    e''1^"E"
    f''1^"F"
  }
  \\layout { }
}
"""


def lily_bass_clef_notes():
    """LilyPond showing bass clef line and space note names."""
    return """\\version "2.24.0"
\\header { tagline = "" }
\\paper {
  indent = 0
  paper-width = 90\\mm
  paper-height = 40\\mm
  top-margin = 2\\mm
  bottom-margin = 2\\mm
  left-margin = 3\\mm
  right-margin = 3\\mm
  ragged-right = ##t
}
\\score {
  \\new Staff {
    \\clef bass
    \\override Staff.TimeSignature.stencil = ##f
    \\override Staff.BarLine.stencil = ##f
    g1^"G"
    a1^"A"
    b1^"B"
    c'1^"C"
    d'1^"D"
    e'1^"E"
    f'1^"F"
    g'1^"G"
    a'1^"A"
  }
  \\layout { }
}
"""


def lily_ledger_lines():
    """LilyPond showing notes on ledger lines above and below the staff."""
    return """\\version "2.24.0"
\\header { tagline = "" }
\\paper {
  indent = 0
  paper-width = 100\\mm
  paper-height = 55\\mm
  top-margin = 4\\mm
  bottom-margin = 4\\mm
  left-margin = 3\\mm
  right-margin = 3\\mm
  ragged-right = ##t
}
\\score {
  \\new PianoStaff <<
    \\new Staff {
      \\clef treble
      \\override Staff.TimeSignature.stencil = ##f
      \\override Staff.BarLine.stencil = ##f
      a''1^"A5 (2 above)"
      g''1^"G5 (1 above)"
      c'1_"C4 (1 below)"
    }
    \\new Staff {
      \\clef bass
      \\override Staff.TimeSignature.stencil = ##f
      \\override Staff.BarLine.stencil = ##f
      c'1^"C4 (1 above)"
      e1_"E2 (1 below)"
      c1_"C2 (2 below)"
    }
  >>
  \\layout { }
}
"""


def lily_chord_inversions(root="c'", third="e'", fifth="g'"):
    """LilyPond showing root position, 1st and 2nd inversions of a triad."""
    return f"""\\version "2.24.0"
\\header {{ tagline = "" }}
\\paper {{
  indent = 0
  paper-width = 80\\mm
  paper-height = 35\\mm
  top-margin = 2\\mm
  bottom-margin = 2\\mm
  left-margin = 3\\mm
  right-margin = 3\\mm
  ragged-right = ##t
}}
\\score {{
  \\new Staff {{
    \\clef treble
    \\override Staff.TimeSignature.stencil = ##f
    \\override Staff.BarLine.stencil = ##f
    <{root} {third} {fifth}>1^"Root"
    <{third} {fifth} {root}'>1^"1st inv."
    <{fifth} {root}' {third}'>1^"2nd inv."
  }}
  \\layout {{ }}
}}
"""


# ─── Q&A Content ─────────────────────────────────────────────────────────────

TOPICS = [
    # ── FUNDAMENTALS ──
    {
        "folder": "01_musical_alphabet",
        "title": "The Musical Alphabet",
        "qa": [
            ("Q: What are the 7 letters used in the musical alphabet?",
             "A: A, B, C, D, E, F, G — then it repeats. These correspond to the 7 white keys on piano before the pattern cycles."),
            ("Q: Why are there only 7 natural note names?",
             "A: The 7 notes come from the diatonic scale — the foundational scale in Western music. The 5 remaining notes (black keys) are sharps/flats of these 7."),
            ("Q: How many total distinct pitches are there before the pattern repeats?",
             "A: 12. Seven natural notes (white keys) plus 5 sharps/flats (black keys) = 12 semitones in one octave."),
            ("Q: What is an octave?",
             "A: An octave is the interval between one note and the next note with the same name (e.g., C4 to C5). The frequency doubles with each octave."),
        ],
    },
    {
        "folder": "02_half_steps_whole_steps",
        "title": "Half Steps and Whole Steps",
        "qa": [
            ("Q: What is a half step (semitone)?",
             "A: The smallest interval in Western music — the distance between any key and the very next key on piano (including black keys). Example: E to F, or C to Db."),
            ("Q: What is a whole step (tone)?",
             "A: Two half steps combined. Example: C to D (skip over Db), or E to F# (skip over F)."),
            ("Q: Where do natural half steps occur (between white keys with no black key in between)?",
             "A: Between E–F and B–C. These are the only pairs of white keys with no black key between them."),
            ("Q: How many half steps are in an octave?",
             "A: 12 half steps."),
        ],
    },
    {
        "folder": "03_chromatic_scale",
        "title": "The Chromatic Scale",
        "qa": [
            ("Q: What is the chromatic scale?",
             "A: A scale that includes all 12 notes in an octave, moving entirely in half steps: C, C#/Db, D, D#/Eb, E, F, F#/Gb, G, G#/Ab, A, A#/Bb, B."),
            ("Q: How many notes are in the chromatic scale?",
             "A: 12 unique pitches."),
            ("Q: What interval separates each note in the chromatic scale?",
             "A: A half step (semitone) — every note is exactly one half step from the next."),
            ("Q: Why is the chromatic scale important?",
             "A: It contains every possible note. All other scales, chords, and keys are subsets of the chromatic scale."),
        ],
    },
    {
        "folder": "04_enharmonic_equivalents",
        "title": "Enharmonic Equivalents",
        "qa": [
            ("Q: What are enharmonic equivalents?",
             "A: Two note names that refer to the same pitch. Example: C# and Db are the same key on piano but spelled differently."),
            ("Q: List all 5 common enharmonic pairs.",
             "A: C#/Db, D#/Eb, F#/Gb, G#/Ab, A#/Bb."),
            ("Q: Why do we need two names for the same note?",
             "A: The correct spelling depends on the key and context. In D major, we write F# (not Gb) because the scale must use each letter once: D-E-F#-G-A-B-C#."),
            ("Q: Can natural notes have enharmonic equivalents?",
             "A: Yes, though rarely used. E = Fb, B = Cb, F = E#, C = B#. These appear in keys like Gb major (which uses Cb) and C# major (which uses B#)."),
        ],
    },
    # ── SCALES & KEYS ──
    {
        "folder": "05_major_scale_formula",
        "title": "The Major Scale Formula",
        "qa": [
            ("Q: What is the interval pattern (formula) for a major scale?",
             "A: W-W-H-W-W-W-H (Whole-Whole-Half-Whole-Whole-Whole-Half)."),
            ("Q: Apply the major scale formula starting on C.",
             "A: C (W) D (W) E (H) F (W) G (W) A (W) B (H) C. All white keys — this is why C major is the simplest key."),
            ("Q: Apply the major scale formula starting on G.",
             "A: G (W) A (W) B (H) C (W) D (W) E (W) F# (H) G. One sharp: F#."),
            ("Q: How many notes are in a major scale?",
             "A: 7 unique notes (8 counting the repeated root at the top)."),
            ("Q: What makes a scale sound 'major'?",
             "A: The major third — the interval of 4 half steps between the 1st and 3rd notes. This creates a bright, happy quality."),
        ],
    },
    {
        "folder": "06_natural_minor_scale",
        "title": "The Natural Minor Scale",
        "qa": [
            ("Q: What is the interval pattern for the natural minor scale?",
             "A: W-H-W-W-H-W-W (Whole-Half-Whole-Whole-Half-Whole-Whole)."),
            ("Q: Apply the natural minor formula starting on A.",
             "A: A (W) B (H) C (W) D (W) E (H) F (W) G (W) A. All white keys — A minor is the 'simplest' minor key."),
            ("Q: What makes a scale sound 'minor'?",
             "A: The minor third — the interval of 3 half steps between the 1st and 3rd notes. This creates a darker, sadder quality."),
            ("Q: How does the minor scale formula compare to major?",
             "A: The 3rd, 6th, and 7th degrees are each lowered by a half step compared to the major scale."),
        ],
    },
    {
        "folder": "07_harmonic_minor_scale",
        "title": "The Harmonic Minor Scale",
        "qa": [
            ("Q: What is the harmonic minor scale?",
             "A: A natural minor scale with the 7th degree raised by a half step. Pattern: W-H-W-W-H-WH-H (WH = augmented 2nd / 3 half steps)."),
            ("Q: Why was the harmonic minor scale created?",
             "A: To create a leading tone (the raised 7th) that pulls strongly to the tonic, enabling a dominant (V) chord in minor keys. The natural minor's flat 7th doesn't create this pull."),
            ("Q: Apply harmonic minor starting on A.",
             "A: A-B-C-D-E-F-G#-A. The G is raised to G#."),
            ("Q: What is the distinctive sound of harmonic minor?",
             "A: The augmented 2nd interval between the 6th and raised 7th (F to G# in A harmonic minor) gives it an exotic, Middle Eastern quality."),
        ],
    },
    {
        "folder": "08_melodic_minor_scale",
        "title": "The Melodic Minor Scale",
        "qa": [
            ("Q: What is the melodic minor scale?",
             "A: A minor scale that raises both the 6th and 7th degrees when ascending, and reverts to natural minor when descending."),
            ("Q: Why raise both the 6th and 7th?",
             "A: To eliminate the awkward augmented 2nd interval in the harmonic minor (between b6 and #7), making melodies smoother."),
            ("Q: Apply melodic minor starting on A (ascending).",
             "A: A-B-C-D-E-F#-G#-A (ascending). A-G-F-E-D-C-B-A (descending = natural minor)."),
            ("Q: In jazz, how is melodic minor used differently?",
             "A: Jazz melodic minor uses the raised 6th and 7th in BOTH directions (ascending and descending). It's sometimes called the 'jazz minor scale.'"),
        ],
    },
    {
        "folder": "09_key_signatures",
        "title": "Key Signatures",
        "qa": [
            ("Q: What is a key signature?",
             "A: A set of sharps or flats at the beginning of a staff that tells you which notes are altered throughout the piece, defining the key."),
            ("Q: How many sharps/flats does each major key have?",
             "A: C=0, G=1#, D=2#, A=3#, E=4#, B=5#, F#=6#, Gb=6b, Db=5b, Ab=4b, Eb=3b, Bb=2b, F=1b."),
            ("Q: What is the order of sharps?",
             "A: F-C-G-D-A-E-B (mnemonic: Father Charles Goes Down And Ends Battle)."),
            ("Q: What is the order of flats?",
             "A: B-E-A-D-G-C-F (reverse of sharps; mnemonic: Battle Ends And Down Goes Charles' Father)."),
            ("Q: Quick trick: How do you identify a sharp key from its signature?",
             "A: The last sharp is the 7th scale degree — go up one half step to find the key. Example: last sharp is F# → key is G major."),
            ("Q: Quick trick: How do you identify a flat key from its signature?",
             "A: The second-to-last flat IS the key. Example: flats are Bb, Eb, Ab → key is Eb major. (Exception: 1 flat = F major.)"),
        ],
    },
    {
        "folder": "10_circle_of_fifths",
        "title": "The Circle of Fifths",
        "qa": [
            ("Q: What is the circle of fifths?",
             "A: A diagram arranging all 12 major (and minor) keys in a circle, where each adjacent key is a perfect 5th apart. Moving clockwise adds one sharp; counterclockwise adds one flat."),
            ("Q: Starting from C, what is the clockwise order?",
             "A: C → G → D → A → E → B → F#/Gb → Db → Ab → Eb → Bb → F → back to C."),
            ("Q: Why is the circle of fifths useful?",
             "A: It shows: (1) how many sharps/flats each key has, (2) which keys are closely related, (3) common chord progressions (adjacent keys share many notes)."),
            ("Q: What are closely related keys?",
             "A: Keys that are adjacent on the circle — they differ by only one sharp or flat and share 6 of 7 notes."),
        ],
    },
    {
        "folder": "11_relative_major_minor",
        "title": "Relative Major and Minor",
        "qa": [
            ("Q: What are relative major and minor keys?",
             "A: A major key and a minor key that share the exact same notes and key signature, but start on different root notes."),
            ("Q: How do you find the relative minor of a major key?",
             "A: Go down 3 half steps (a minor 3rd) from the major key's root. Example: C major → A minor."),
            ("Q: How do you find the relative major of a minor key?",
             "A: Go up 3 half steps from the minor key's root. Example: A minor → C major."),
            ("Q: List all relative major/minor pairs.",
             "A: C/Am, G/Em, D/Bm, A/F#m, E/C#m, B/G#m, Gb/Ebm, Db/Bbm, Ab/Fm, Eb/Cm, Bb/Gm, F/Dm."),
            ("Q: If two keys share the same notes, how do they sound different?",
             "A: The tonal center (which note feels like 'home') is different. C major gravitates to C; A minor gravitates to A. This changes the mood from bright (major) to dark (minor)."),
        ],
    },
    # ── INTERVALS ──
    {
        "folder": "12_what_intervals_are",
        "title": "What Intervals Are",
        "qa": [
            ("Q: What is a musical interval?",
             "A: The distance in pitch between two notes, measured by counting the letter names and half steps between them."),
            ("Q: What is the difference between a melodic and harmonic interval?",
             "A: Melodic = two notes played one after the other. Harmonic = two notes played simultaneously."),
            ("Q: How are intervals named?",
             "A: By a number (the letter-name distance: 2nd, 3rd, 4th, etc.) and a quality (major, minor, perfect, augmented, diminished)."),
            ("Q: What is a unison?",
             "A: An interval of zero — two identical pitches sounding together or in sequence."),
        ],
    },
    {
        "folder": "13_interval_qualities",
        "title": "Interval Qualities",
        "qa": [
            ("Q: Which intervals can be 'perfect'?",
             "A: Unisons (1st), 4ths, 5ths, and octaves (8ths). These intervals sound the most consonant/stable."),
            ("Q: Which intervals use 'major' and 'minor'?",
             "A: 2nds, 3rds, 6ths, and 7ths. Major is one half step wider than minor."),
            ("Q: What does 'augmented' mean?",
             "A: One half step wider than a perfect or major interval. Example: perfect 5th (7 semitones) → augmented 5th (8 semitones)."),
            ("Q: What does 'diminished' mean?",
             "A: One half step narrower than a perfect or minor interval. Example: perfect 5th (7 semitones) → diminished 5th (6 semitones)."),
            ("Q: What is the tritone?",
             "A: An interval of exactly 6 half steps (augmented 4th / diminished 5th). It splits the octave in half and sounds tense/unstable. It's called 'tri-tone' because it spans three whole tones."),
        ],
    },
    {
        "folder": "14_interval_recognition",
        "title": "Interval Recognition",
        "qa": [
            ("Q: How many half steps is a minor 2nd (m2)?", "A: 1 half step. Example: C to Db."),
            ("Q: How many half steps is a major 2nd (M2)?", "A: 2 half steps. Example: C to D."),
            ("Q: How many half steps is a minor 3rd (m3)?", "A: 3 half steps. Example: C to Eb."),
            ("Q: How many half steps is a major 3rd (M3)?", "A: 4 half steps. Example: C to E."),
            ("Q: How many half steps is a perfect 4th (P4)?", "A: 5 half steps. Example: C to F."),
            ("Q: How many half steps is a tritone (aug4/dim5)?", "A: 6 half steps. Example: C to F#/Gb."),
            ("Q: How many half steps is a perfect 5th (P5)?", "A: 7 half steps. Example: C to G."),
            ("Q: How many half steps is a minor 6th (m6)?", "A: 8 half steps. Example: C to Ab."),
            ("Q: How many half steps is a major 6th (M6)?", "A: 9 half steps. Example: C to A."),
            ("Q: How many half steps is a minor 7th (m7)?", "A: 10 half steps. Example: C to Bb."),
            ("Q: How many half steps is a major 7th (M7)?", "A: 11 half steps. Example: C to B."),
            ("Q: How many half steps is a perfect octave (P8)?", "A: 12 half steps. Example: C to C."),
        ],
    },
    # ── CHORD CONSTRUCTION ──
    {
        "folder": "15_what_a_triad_is",
        "title": "What a Triad Is",
        "qa": [
            ("Q: What is a triad?",
             "A: A three-note chord built by stacking two intervals of a third (every other note in a scale). The notes are called root, third, and fifth."),
            ("Q: Why are they called root, third, and fifth?",
             "A: Root = the foundation note the chord is named after. Third = 3 letter names above the root. Fifth = 5 letter names above the root."),
            ("Q: How many types of triads exist?",
             "A: Four: major, minor, diminished, and augmented. These come from all possible combinations of stacking major and minor thirds."),
        ],
    },
    {
        "folder": "16_major_triad",
        "title": "Major Triad Formula",
        "qa": [
            ("Q: What is the formula for a major triad?",
             "A: Root + Major 3rd + Perfect 5th. In semitones from root: 0-4-7."),
            ("Q: How is a major triad built in terms of stacked thirds?",
             "A: Major 3rd (4 semitones) on bottom + Minor 3rd (3 semitones) on top = 4+3."),
            ("Q: Build a C major triad.",
             "A: C (root) + E (major 3rd, 4 semitones up) + G (perfect 5th, 7 semitones up) = C-E-G."),
            ("Q: What quality/mood does a major triad have?",
             "A: Bright, happy, stable, resolved."),
        ],
    },
    {
        "folder": "17_minor_triad",
        "title": "Minor Triad Formula",
        "qa": [
            ("Q: What is the formula for a minor triad?",
             "A: Root + Minor 3rd + Perfect 5th. In semitones from root: 0-3-7."),
            ("Q: How is a minor triad built in terms of stacked thirds?",
             "A: Minor 3rd (3 semitones) on bottom + Major 3rd (4 semitones) on top = 3+4."),
            ("Q: Build a C minor triad.",
             "A: C (root) + Eb (minor 3rd, 3 semitones up) + G (perfect 5th, 7 semitones up) = C-Eb-G."),
            ("Q: What is the only difference between a major and minor triad?",
             "A: The third is lowered by one half step. The root and fifth stay the same. (C-E-G → C-Eb-G)"),
        ],
    },
    {
        "folder": "18_diminished_triad",
        "title": "Diminished Triad Formula",
        "qa": [
            ("Q: What is the formula for a diminished triad?",
             "A: Root + Minor 3rd + Diminished 5th. In semitones from root: 0-3-6."),
            ("Q: How is a diminished triad built in terms of stacked thirds?",
             "A: Minor 3rd (3 semitones) + Minor 3rd (3 semitones) = 3+3."),
            ("Q: Build a B diminished triad.",
             "A: B-D-F. This naturally occurs as the vii° chord in C major."),
            ("Q: What quality/mood does a diminished triad have?",
             "A: Tense, unstable, dissonant — it strongly wants to resolve to another chord."),
        ],
    },
    {
        "folder": "19_augmented_triad",
        "title": "Augmented Triad Formula",
        "qa": [
            ("Q: What is the formula for an augmented triad?",
             "A: Root + Major 3rd + Augmented 5th. In semitones from root: 0-4-8."),
            ("Q: How is an augmented triad built in terms of stacked thirds?",
             "A: Major 3rd (4 semitones) + Major 3rd (4 semitones) = 4+4."),
            ("Q: Build a C augmented triad.",
             "A: C-E-G# (the fifth is raised one half step from a major triad)."),
            ("Q: What is unique about augmented triads?",
             "A: They divide the octave into three equal parts (every 4 semitones). There are only 4 distinct augmented triads — C aug, Db aug, D aug, Eb aug — after that they repeat as inversions."),
        ],
    },
    {
        "folder": "20_why_four_triad_types",
        "title": "Why These Four Triad Types Exist",
        "qa": [
            ("Q: Why are there exactly four types of triads?",
             "A: A triad is two stacked thirds. Each third can be major (M3=4 semitones) or minor (m3=3 semitones). That gives 2×2=4 combinations:\n"
             "   M3+m3 = Major\n   m3+M3 = Minor\n   m3+m3 = Diminished\n   M3+M3 = Augmented"),
            ("Q: Summarize all four triad formulas in semitones.",
             "A: Major: 0-4-7 | Minor: 0-3-7 | Diminished: 0-3-6 | Augmented: 0-4-8."),
            ("Q: Which triads have a perfect 5th?",
             "A: Major and minor. The diminished 5th is one half step lower; the augmented 5th is one half step higher."),
        ],
    },
    {
        "folder": "21_seventh_chords",
        "title": "Seventh Chord Types",
        "qa": [
            ("Q: What is a seventh chord?",
             "A: A four-note chord: a triad plus one more third stacked on top (the 7th degree above the root)."),
            ("Q: What are the 5 common seventh chord types?",
             "A: Major 7 (Maj7), Dominant 7 (Dom7), Minor 7 (Min7), Half-Diminished 7 (m7b5), Fully Diminished 7 (dim7)."),
            ("Q: Major 7th (Maj7) — formula?",
             "A: Major triad + Major 7th. Semitones: 0-4-7-11. Example: CMaj7 = C-E-G-B. Sound: dreamy, jazzy, lush."),
            ("Q: Dominant 7th (Dom7) — formula?",
             "A: Major triad + Minor 7th. Semitones: 0-4-7-10. Example: C7 = C-E-G-Bb. Sound: bluesy, wants to resolve."),
            ("Q: Minor 7th (Min7) — formula?",
             "A: Minor triad + Minor 7th. Semitones: 0-3-7-10. Example: Cm7 = C-Eb-G-Bb. Sound: mellow, smooth, jazzy."),
            ("Q: Half-Diminished 7th (m7b5 / ø7) — formula?",
             "A: Diminished triad + Minor 7th. Semitones: 0-3-6-10. Example: Cø7 = C-Eb-Gb-Bb. Sound: dark, yearning."),
            ("Q: Fully Diminished 7th (dim7 / °7) — formula?",
             "A: Diminished triad + Diminished 7th. Semitones: 0-3-6-9. Example: Cdim7 = C-Eb-Gb-Bbb(=A). Sound: very tense, symmetrical (divides octave into 4 equal parts)."),
        ],
    },
    {
        "folder": "22_chord_inversions",
        "title": "Chord Inversions",
        "qa": [
            ("Q: What is a chord inversion?",
             "A: A rearrangement of a chord's notes so that a note other than the root is in the bass (lowest position)."),
            ("Q: What is root position?",
             "A: The root is the lowest note. Example: C-E-G (C is on the bottom)."),
            ("Q: What is first inversion?",
             "A: The third is the lowest note. Example: E-G-C (the C has been moved up an octave)."),
            ("Q: What is second inversion?",
             "A: The fifth is the lowest note. Example: G-C-E (the C and E have been moved up)."),
            ("Q: Why are inversions useful?",
             "A: They create smoother voice leading between chords (less jumping), different bass lines, and varied textures — even though the chord name and function stay the same."),
            ("Q: How are inversions notated in figured bass?",
             "A: Root position = 5/3 (or just the chord name). 1st inversion = 6/3 (or 6). 2nd inversion = 6/4. Example: C/E means C major with E in the bass (1st inversion)."),
        ],
    },
    # ── CHORDS IN KEYS (HARMONY) ──
    {
        "folder": "23_diatonic_chords",
        "title": "Diatonic Chords",
        "qa": [
            ("Q: What are diatonic chords?",
             "A: Chords built using ONLY the notes of a given key/scale. You stack thirds on each scale degree."),
            ("Q: Build the diatonic triads of C major.",
             "A: C (C-E-G), Dm (D-F-A), Em (E-G-B), F (F-A-C), G (G-B-D), Am (A-C-E), Bdim (B-D-F)."),
            ("Q: What is the pattern of chord qualities in ANY major key?",
             "A: I=Major, ii=minor, iii=minor, IV=Major, V=Major, vi=minor, vii°=diminished."),
            ("Q: Why do different scale degrees produce different chord types?",
             "A: Because the spacing of whole and half steps in the scale creates different third combinations on each degree. For example, starting on the 2nd degree stacks a minor 3rd then a major 3rd, making it minor."),
        ],
    },
    {
        "folder": "24_roman_numeral_analysis",
        "title": "Roman Numeral Analysis",
        "qa": [
            ("Q: What do Roman numerals represent in music theory?",
             "A: The scale degree a chord is built on AND its quality. Uppercase = major, lowercase = minor, ° = diminished, + = augmented."),
            ("Q: What are the 7 Roman numerals for a major key?",
             "A: I  ii  iii  IV  V  vi  vii°"),
            ("Q: What are the 7 Roman numerals for a natural minor key?",
             "A: i  ii°  III  iv  v  VI  VII"),
            ("Q: Why use Roman numerals instead of chord names?",
             "A: They describe chord FUNCTION independent of key. 'V → I' means the same resolution in every key (G→C in C major, D→G in G major, etc.)."),
            ("Q: What does 'V7' mean?",
             "A: A dominant 7th chord built on the 5th scale degree. In C major: G-B-D-F (G7)."),
        ],
    },
    {
        "folder": "25_why_major_minor_in_key",
        "title": "Why Some Chords Are Major and Others Minor",
        "qa": [
            ("Q: In C major, why is the I chord major and the ii chord minor?",
             "A: Stack thirds using only C major notes:\n"
             "   I: C-E-G → C to E = 4 semitones (M3) → Major\n"
             "   ii: D-F-A → D to F = 3 semitones (m3) → Minor\n"
             "   The scale's half/whole step pattern determines each chord's quality."),
            ("Q: Why is vii° diminished?",
             "A: Building on B in C major: B-D-F. B to D = 3 semitones (m3), D to F = 3 semitones (m3). Two stacked minor thirds = diminished."),
            ("Q: Is this pattern the same in every major key?",
             "A: Yes! The quality pattern I-ii-iii-IV-V-vi-vii° holds for ALL major keys because the W-W-H-W-W-W-H interval structure is always the same."),
        ],
    },
    {
        "folder": "26_dominant_tonic_resolution",
        "title": "The V–I (Dominant–Tonic) Resolution",
        "qa": [
            ("Q: What is the V–I resolution?",
             "A: The strongest harmonic pull in tonal music — the dominant chord (V or V7) resolving to the tonic (I). Example in C major: G(7) → C."),
            ("Q: Why is V→I so powerful?",
             "A: The V chord contains the leading tone (7th scale degree, just one half step below the root), which desperately wants to resolve upward to the tonic. In V7, the tritone between the 3rd and 7th creates extra tension."),
            ("Q: What is the leading tone?",
             "A: The 7th degree of the major scale, one half step below the tonic. In C major: B → C. This pull is the engine of tonal harmony."),
            ("Q: What is a half cadence vs. an authentic cadence?",
             "A: Authentic cadence = V → I (feels resolved, final). Half cadence = ending on V (feels incomplete, like a question mark)."),
        ],
    },
    {
        "folder": "27_common_progressions",
        "title": "Common Chord Progressions",
        "qa": [
            ("Q: What is the I–IV–V–I progression?",
             "A: The most fundamental progression in Western music. In C: C→F→G→C. Used in blues, rock, folk, classical."),
            ("Q: What is the I–V–vi–IV progression?",
             "A: The 'pop' progression — used in hundreds of hit songs. In C: C→G→Am→F."),
            ("Q: What is the ii–V–I progression?",
             "A: The most important progression in jazz. In C: Dm7→G7→CMaj7. The ii sets up the V, which resolves to I."),
            ("Q: What is the 12-bar blues progression?",
             "A: I-I-I-I / IV-IV-I-I / V-IV-I-I (or V). A 12-bar repeating form that is the foundation of blues, early rock, and jazz."),
            ("Q: What is a vi–IV–I–V progression?",
             "A: A rotation of the pop progression starting on the minor chord. In C: Am→F→C→G. Common in emotional pop/rock ballads."),
            ("Q: What makes a progression sound 'good'?",
             "A: Strong progressions follow voice-leading principles — shared tones between chords, stepwise bass motion, and tension-resolution cycles (especially V→I)."),
        ],
    },
    # ── READING MUSIC ──
    {
        "folder": "28_treble_clef_notes",
        "title": "Treble Clef Note Positions",
        "qa": [
            ("Q: What are the notes on the lines of the treble clef (bottom to top)?",
             "A: E-G-B-D-F. Mnemonic: Every Good Boy Does Fine."),
            ("Q: What are the notes in the spaces of the treble clef (bottom to top)?",
             "A: F-A-C-E. Mnemonic: it spells FACE."),
            ("Q: What note is on the first ledger line below the treble clef?",
             "A: Middle C (C4)."),
            ("Q: What does the treble clef symbol indicate?",
             "A: It's also called the G-clef — the curl wraps around the second line, marking it as G4."),
        ],
    },
    {
        "folder": "29_bass_clef_notes",
        "title": "Bass Clef Note Positions",
        "qa": [
            ("Q: What are the notes on the lines of the bass clef (bottom to top)?",
             "A: G-B-D-F-A. Mnemonic: Good Boys Do Fine Always."),
            ("Q: What are the notes in the spaces of the bass clef (bottom to top)?",
             "A: A-C-E-G. Mnemonic: All Cows Eat Grass."),
            ("Q: What note is on the first ledger line above the bass clef?",
             "A: Middle C (C4)."),
            ("Q: What does the bass clef symbol indicate?",
             "A: It's also called the F-clef — the two dots surround the fourth line, marking it as F3."),
        ],
    },
    {
        "folder": "30_ledger_lines",
        "title": "Ledger Lines",
        "qa": [
            ("Q: What are ledger lines?",
             "A: Short horizontal lines added above or below the staff to extend its range for notes that don't fit on the 5 lines and 4 spaces."),
            ("Q: Where is middle C on the grand staff?",
             "A: On one ledger line — it sits between the treble and bass staves. It's one ledger line below the treble staff or one ledger line above the bass staff."),
            ("Q: What is 8va/8vb notation?",
             "A: 8va (ottava alta) = play one octave higher than written. 8vb (ottava bassa) = play one octave lower. Used to avoid excessive ledger lines."),
        ],
    },
    {
        "folder": "31_note_durations",
        "title": "Note Durations",
        "qa": [
            ("Q: What are the standard note durations from longest to shortest?",
             "A: Whole (4 beats) → Half (2 beats) → Quarter (1 beat) → Eighth (1/2 beat) → Sixteenth (1/4 beat)."),
            ("Q: How do note durations relate to each other?",
             "A: Each duration is exactly half the previous: 1 whole = 2 halves = 4 quarters = 8 eighths = 16 sixteenths."),
            ("Q: What does a dot after a note do?",
             "A: Adds half the note's value. A dotted half note = 2 + 1 = 3 beats. A dotted quarter = 1 + 0.5 = 1.5 beats."),
            ("Q: What is a tie?",
             "A: A curved line connecting two notes of the same pitch, combining their durations. A half note tied to a quarter note = 3 beats."),
            ("Q: How do you identify note types visually?",
             "A: Whole = open notehead, no stem. Half = open notehead + stem. Quarter = filled notehead + stem. Eighth = filled + stem + 1 flag. Sixteenth = filled + stem + 2 flags."),
        ],
    },
    {
        "folder": "32_time_signatures",
        "title": "Time Signatures",
        "qa": [
            ("Q: What does a time signature tell you?",
             "A: The top number = how many beats per measure. The bottom number = which note value gets one beat."),
            ("Q: What does 4/4 mean?",
             "A: 4 beats per measure, quarter note = 1 beat. Also called 'common time' (notated as C). The most common time signature."),
            ("Q: What does 3/4 mean?",
             "A: 3 beats per measure, quarter note = 1 beat. Creates a waltz feel (ONE-two-three)."),
            ("Q: What does 6/8 mean?",
             "A: 6 eighth notes per measure, grouped as two groups of 3. Creates a compound feel (ONE-two-three-FOUR-five-six). Different from 3/4 despite having similar duration per measure."),
            ("Q: What is the difference between simple and compound time?",
             "A: Simple time: beats divide into 2 (2/4, 3/4, 4/4). Compound time: beats divide into 3 (6/8, 9/8, 12/8)."),
        ],
    },
    {
        "folder": "33_rests",
        "title": "Rests",
        "qa": [
            ("Q: What is a rest?",
             "A: A symbol indicating silence for a specific duration. Each note duration has a corresponding rest of equal length."),
            ("Q: What does a whole rest look like?",
             "A: A filled rectangle hanging DOWN from the 4th line (looks like a hat). Worth 4 beats (or fills an entire measure in any time signature)."),
            ("Q: What does a half rest look like?",
             "A: A filled rectangle sitting UP on the 3rd line (looks like a top hat). Worth 2 beats."),
            ("Q: How do you tell a whole rest from a half rest?",
             "A: Whole rest hangs down (heavy, like a 'whole' weight). Half rest sits up (lighter, 'half' the weight)."),
            ("Q: What do quarter, eighth, and sixteenth rests look like?",
             "A: Quarter rest = zigzag line. Eighth rest = diagonal line with one flag. Sixteenth rest = diagonal line with two flags."),
        ],
    },
]


# ─── Image generation per topic ─────────────────────────────────────────────

def generate_topic_images(topic, topic_dir):
    """Generate visual assets for a given topic."""
    folder = topic["folder"]

    # Chromatic note to MIDI (in octave 4)
    NOTE_TO_MIDI = {name: 60 + i for i, name in enumerate(NOTE_NAMES)}

    if folder == "01_musical_alphabet":
        # Keyboard with white keys labeled
        midis = [60, 62, 64, 65, 67, 69, 71, 72]  # C4 through C5
        annotations = {}
        for m in midis:
            annotations[m] = NOTE_NAMES[m % 12]
        draw_zoomed_keyboard(midis, os.path.join(topic_dir, "keyboard.png"),
                             label="The Musical Alphabet: A B C D E F G",
                             annotations=annotations, center_midi=66, span_semitones=16)

    elif folder == "02_half_steps_whole_steps":
        # Show half steps E-F, B-C and whole step C-D, D-E
        steps = [
            ("H", 64, 65),  # E-F
            ("H", 71, 72),  # B-C
            ("W", 60, 62),  # C-D
            ("W", 62, 64),  # D-E
        ]
        all_midis = set()
        for _, a, b in steps:
            all_midis.update([a, b])
        draw_step_diagram(os.path.join(topic_dir, "diagram.png"), steps,
                          label="Half Steps (red) and Whole Steps (green)")

    elif folder == "03_chromatic_scale":
        # All 12 notes highlighted in one octave
        midis = list(range(60, 73))  # C4 to C5 (13 notes)
        annotations = {}
        for m in midis:
            annotations[m] = NOTE_NAMES[m % 12]
        draw_zoomed_keyboard(midis, os.path.join(topic_dir, "keyboard.png"),
                             label="The Chromatic Scale: All 12 Notes",
                             annotations=annotations, center_midi=66, span_semitones=18)

    elif folder == "04_enharmonic_equivalents":
        # Highlight black keys with both names
        enharmonic = {61: "C#/Db", 63: "D#/Eb", 66: "F#/Gb", 68: "G#/Ab", 70: "A#/Bb"}
        draw_zoomed_keyboard(list(enharmonic.keys()),
                             os.path.join(topic_dir, "keyboard.png"),
                             label="Enharmonic Equivalents",
                             annotations=enharmonic, center_midi=66, span_semitones=16)

    elif folder == "05_major_scale_formula":
        # C major scale with W/H steps
        c_major_midis = [60, 62, 64, 65, 67, 69, 71, 72]
        steps = [
            ("W", 60, 62), ("W", 62, 64), ("H", 64, 65),
            ("W", 65, 67), ("W", 67, 69), ("W", 69, 71), ("H", 71, 72),
        ]
        draw_step_diagram(os.path.join(topic_dir, "c_major.png"), steps,
                          label="C Major Scale: W-W-H-W-W-W-H")

        # G major scale
        g_major_midis = [67, 69, 71, 72, 74, 76, 78, 79]
        steps_g = [
            ("W", 67, 69), ("W", 69, 71), ("H", 71, 72),
            ("W", 72, 74), ("W", 74, 76), ("W", 76, 78), ("H", 78, 79),
        ]
        draw_step_diagram(os.path.join(topic_dir, "g_major.png"), steps_g,
                          label="G Major Scale: W-W-H-W-W-W-H")

    elif folder == "06_natural_minor_scale":
        # A natural minor
        steps = [
            ("W", 69, 71), ("H", 71, 72), ("W", 72, 74),
            ("W", 74, 76), ("H", 76, 77), ("W", 77, 79), ("W", 79, 81),
        ]
        draw_step_diagram(os.path.join(topic_dir, "a_minor.png"), steps,
                          label="A Natural Minor: W-H-W-W-H-W-W")

    elif folder == "07_harmonic_minor_scale":
        # A harmonic minor: A-B-C-D-E-F-G#-A
        midis = [69, 71, 72, 74, 76, 77, 80, 81]
        annotations = {69: "A", 71: "B", 72: "C", 74: "D", 76: "E", 77: "F", 80: "G#", 81: "A"}
        draw_zoomed_keyboard(midis, os.path.join(topic_dir, "a_harmonic_minor.png"),
                             label="A Harmonic Minor: raised 7th (G→G#)",
                             annotations=annotations, center_midi=75, span_semitones=18)

    elif folder == "08_melodic_minor_scale":
        # A melodic minor ascending: A-B-C-D-E-F#-G#-A
        midis = [69, 71, 72, 74, 76, 78, 80, 81]
        annotations = {69: "A", 71: "B", 72: "C", 74: "D", 76: "E", 78: "F#", 80: "G#", 81: "A"}
        draw_zoomed_keyboard(midis, os.path.join(topic_dir, "a_melodic_minor.png"),
                             label="A Melodic Minor (ascending): raised 6th & 7th",
                             annotations=annotations, center_midi=75, span_semitones=18)

    elif folder == "09_key_signatures":
        # Generate LilyPond key signature images for a few representative keys
        key_sigs = [
            ("C", "major", "C Major (0 sharps/flats)"),
            ("G", "major", "G Major (1 sharp)"),
            ("D", "major", "D Major (2 sharps)"),
            ("A", "major", "A Major (3 sharps)"),
            ("E", "major", "E Major (4 sharps)"),
            ("B", "major", "B Major (5 sharps)"),
            ("F", "major", "F Major (1 flat)"),
            ("Bb", "major", "Bb Major (2 flats)"),
            ("Eb", "major", "Eb Major (3 flats)"),
            ("Ab", "major", "Ab Major (4 flats)"),
            ("Db", "major", "Db Major (5 flats)"),
            ("Gb", "major", "Gb Major (6 flats)"),
        ]
        for key_name, mode, display in key_sigs:
            safe_name = key_name.replace("#", "sharp").replace("b", "flat")
            lily = lily_key_signature(key_name, mode)
            out_path = os.path.join(topic_dir, f"key_{safe_name}_{mode}.png")
            if render_lily_custom(lily, out_path):
                print(f"    key sig: {display}")

    elif folder == "10_circle_of_fifths":
        draw_circle_of_fifths(os.path.join(topic_dir, "circle_of_fifths.png"))

    elif folder == "11_relative_major_minor":
        # Show C major and A minor share the same notes
        c_major = [60, 62, 64, 65, 67, 69, 71]
        annotations = {60: "C", 62: "D", 64: "E", 65: "F", 67: "G", 69: "A", 71: "B"}
        draw_zoomed_keyboard(c_major, os.path.join(topic_dir, "c_major_a_minor.png"),
                             label="C Major / A Minor: same notes, different home",
                             annotations=annotations, center_midi=66, span_semitones=16)

    elif folder == "14_interval_recognition":
        # Generate a keyboard image for each interval from C
        intervals = [
            ("minor_2nd", 1, "C to Db"), ("major_2nd", 2, "C to D"),
            ("minor_3rd", 3, "C to Eb"), ("major_3rd", 4, "C to E"),
            ("perfect_4th", 5, "C to F"), ("tritone", 6, "C to Gb"),
            ("perfect_5th", 7, "C to G"), ("minor_6th", 8, "C to Ab"),
            ("major_6th", 9, "C to A"), ("minor_7th", 10, "C to Bb"),
            ("major_7th", 11, "C to B"), ("perfect_8th", 12, "C to C"),
        ]
        for name, semitones, desc in intervals:
            midis = [60, 60 + semitones]
            annotations = {60: "C", 60 + semitones: NOTE_NAMES[(60 + semitones) % 12]}
            draw_zoomed_keyboard(midis,
                                 os.path.join(topic_dir, f"interval_{name}.png"),
                                 label=f"{name}: {desc} ({semitones} semitones)",
                                 annotations=annotations, center_midi=66, span_semitones=18)

    elif folder == "22_chord_inversions":
        # LilyPond showing C major inversions
        lily = lily_chord_inversions("c'", "e'", "g'")
        render_lily_custom(lily, os.path.join(topic_dir, "c_major_inversions.png"))

        # Keyboard diagrams for each inversion
        draw_zoomed_keyboard([60, 64, 67], os.path.join(topic_dir, "root_position.png"),
                             label="Root Position: C-E-G",
                             annotations={60: "C", 64: "E", 67: "G"},
                             center_midi=64, span_semitones=14)
        draw_zoomed_keyboard([64, 67, 72], os.path.join(topic_dir, "first_inversion.png"),
                             label="1st Inversion: E-G-C",
                             annotations={64: "E", 67: "G", 72: "C"},
                             center_midi=68, span_semitones=14)
        draw_zoomed_keyboard([67, 72, 76], os.path.join(topic_dir, "second_inversion.png"),
                             label="2nd Inversion: G-C-E",
                             annotations={67: "G", 72: "C", 76: "E"},
                             center_midi=72, span_semitones=14)

    elif folder == "23_diatonic_chords":
        # Show all 7 diatonic triads of C major on keyboard
        diatonic = [
            ("I: C", [60, 64, 67]),
            ("ii: Dm", [62, 65, 69]),
            ("iii: Em", [64, 67, 71]),
            ("IV: F", [65, 69, 72]),
            ("V: G", [67, 71, 74]),
            ("vi: Am", [69, 72, 76]),
            ("vii°: Bdim", [71, 74, 77]),
        ]
        for label, midis in diatonic:
            safe = label.split(":")[0].strip().replace("°", "dim")
            annotations = {m: NOTE_NAMES[m % 12] for m in midis}
            draw_zoomed_keyboard(midis,
                                 os.path.join(topic_dir, f"diatonic_{safe}.png"),
                                 label=f"C Major — {label}",
                                 annotations=annotations,
                                 center_midi=68, span_semitones=22)

    elif folder == "28_treble_clef_notes":
        lily = lily_treble_clef_notes()
        render_lily_custom(lily, os.path.join(topic_dir, "treble_clef_notes.png"))

    elif folder == "29_bass_clef_notes":
        lily = lily_bass_clef_notes()
        render_lily_custom(lily, os.path.join(topic_dir, "bass_clef_notes.png"))

    elif folder == "30_ledger_lines":
        lily = lily_ledger_lines()
        render_lily_custom(lily, os.path.join(topic_dir, "ledger_lines.png"))

    elif folder == "31_note_durations":
        lily = lily_note_durations()
        render_lily_custom(lily, os.path.join(topic_dir, "note_durations.png"))

    elif folder == "32_time_signatures":
        lily = lily_time_signatures()
        render_lily_custom(lily, os.path.join(topic_dir, "time_signatures.png"))

    elif folder == "33_rests":
        lily = lily_rests()
        render_lily_custom(lily, os.path.join(topic_dir, "rests.png"))


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(THEORY_DIR, exist_ok=True)

    for topic in TOPICS:
        folder = topic["folder"]
        title = topic["title"]
        qa_pairs = topic["qa"]

        topic_dir = os.path.join(THEORY_DIR, folder)
        os.makedirs(topic_dir, exist_ok=True)

        # Write Q&A file
        qa_path = os.path.join(topic_dir, "qa.txt")
        with open(qa_path, "w") as f:
            f.write(f"# {title}\n\n")
            for i, (q, a) in enumerate(qa_pairs, 1):
                f.write(f"---\n{q}\n\n{a}\n\n")

        print(f"[{folder}] {title} — {len(qa_pairs)} Q&A pairs")

        # Generate images
        try:
            generate_topic_images(topic, topic_dir)
        except Exception as e:
            print(f"  Image generation error: {e}")

    print(f"\nDone! Generated {len(TOPICS)} theory topics in {THEORY_DIR}")


if __name__ == "__main__":
    main()
