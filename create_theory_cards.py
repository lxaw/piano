#!/usr/bin/env python3
"""Create Anki cards for all piano theory topics.

Card format:
  Front: Question text + topic title
  Back:  Answer text + all related diagrams/images for that topic

Requires Anki open with AnkiConnect add-on installed.
"""

import os
import re
from time import sleep

from anki_commands import invoke

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THEORY_DIR = os.path.join(BASE_DIR, "assets", "theory")

# ─── Config ───────────────────────────────────────────────────────────────────

DECK_NAME = "Piano::Theory"
MODEL_NAME = "PianoTheoryQA"

CARD_CSS = """\
.card {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 20px;
    text-align: center;
    color: #333;
    background-color: #fafafa;
    padding: 20px;
    max-width: 700px;
    margin: 0 auto;
}
.topic {
    font-size: 14px;
    color: #999;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.question {
    font-size: 24px;
    font-weight: bold;
    color: #222;
    margin: 20px 0;
    line-height: 1.4;
}
.answer {
    font-size: 20px;
    color: #333;
    text-align: left;
    margin: 16px auto;
    max-width: 600px;
    line-height: 1.6;
    white-space: pre-line;
}
.images {
    margin-top: 16px;
}
.images img {
    max-width: 100%;
    max-height: 400px;
    margin: 8px auto;
    display: block;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}
"""

FRONT_TEMPLATE = """\
<div class="card">
<div class="topic">{{Topic}}</div>
<div class="question">{{Question}}</div>
</div>
"""

BACK_TEMPLATE = """\
<div class="card">
<div class="topic">{{Topic}}</div>
<div class="question">{{Question}}</div>
<hr id="answer">
<div class="answer">{{Answer}}</div>
<div class="images">{{Images}}</div>
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
        inOrderFields=["Question", "Topic", "Answer", "Images"],
        css=CARD_CSS,
        cardTemplates=[{
            "Name": "Question → Answer",
            "Front": FRONT_TEMPLATE,
            "Back": BACK_TEMPLATE,
        }],
    )
    print(f"Model '{MODEL_NAME}' created.")


# ─── Parse qa.txt ─────────────────────────────────────────────────────────────

def parse_qa_file(qa_path):
    """Parse qa.txt and return list of (question, answer) tuples."""
    with open(qa_path, "r") as f:
        content = f.read()

    # Extract title from first line
    title = ""
    lines = content.split("\n")
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Split by --- separators
    blocks = re.split(r"^---$", content, flags=re.MULTILINE)

    qa_pairs = []
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("#"):
            continue

        # Find Q: and A: lines
        q_match = re.search(r"^Q:\s*(.+?)$", block, re.MULTILINE)
        a_match = re.search(r"^A:\s*(.+)", block, re.MULTILINE | re.DOTALL)

        if q_match and a_match:
            question = q_match.group(1).strip()
            answer = a_match.group(1).strip()
            qa_pairs.append((question, answer))

    return title, qa_pairs


# ─── Card creation ────────────────────────────────────────────────────────────

def create_theory_cards_for_topic(topic_folder):
    """Create all Q&A cards for a single theory topic."""
    topic_dir = os.path.join(THEORY_DIR, topic_folder)
    qa_path = os.path.join(topic_dir, "qa.txt")

    if not os.path.exists(qa_path):
        return 0

    title, qa_pairs = parse_qa_file(qa_path)
    if not qa_pairs:
        return 0

    # Collect all images in this topic folder
    image_files = sorted([
        f for f in os.listdir(topic_dir)
        if f.endswith(".png") and not f.startswith(".")
    ])

    # Store images in Anki media and build HTML
    images_html_parts = []
    picture_attachments = []

    for img_file in image_files:
        img_path = os.path.join(topic_dir, img_file)
        anki_filename = f"piano_theory_{topic_folder}_{img_file}"
        images_html_parts.append(f'<img src="{anki_filename}">')
        picture_attachments.append({
            "path": os.path.abspath(img_path),
            "filename": anki_filename,
            "fields": [],
        })

    images_html = "\n".join(images_html_parts)

    created = 0
    for question, answer in qa_pairs:
        note = {
            "deckName": DECK_NAME,
            "modelName": MODEL_NAME,
            "fields": {
                "Topic": title,
                "Question": question,
                "Answer": answer,
                "Images": images_html,
            },
            "options": {"allowDuplicate": False},
            "picture": list(picture_attachments),  # copy the list
            "audio": [],
        }

        try:
            invoke("addNote", note=note)
            created += 1
        except Exception as e:
            err_msg = str(e)
            if "duplicate" in err_msg.lower():
                pass  # skip silently
            else:
                raise

    return created


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Get all theory topic folders in order
    topic_folders = sorted([
        d for d in os.listdir(THEORY_DIR)
        if os.path.isdir(os.path.join(THEORY_DIR, d))
    ])

    print(f"Found {len(topic_folders)} theory topics.\n")

    ensure_deck()
    ensure_model()

    total_cards = 0
    errors = []

    for i, folder in enumerate(topic_folders, 1):
        try:
            count = create_theory_cards_for_topic(folder)
            total_cards += count
            print(f"  [{i}/{len(topic_folders)}] {folder} — {count} cards ✓")
        except Exception as e:
            print(f"  [{i}/{len(topic_folders)}] {folder} ✗ — {e}")
            errors.append(folder)
        sleep(0.05)

    print(f"\nDone! Created {total_cards} theory cards across {len(topic_folders)} topics.")
    if errors:
        print(f"Errors in: {', '.join(errors)}")


if __name__ == "__main__":
    main()
