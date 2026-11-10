"""Read-only import of the first native Web chapter; never edits the Godot tree."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"D:\dachuang\naxi-game")
CONTENT = SOURCE / "Data/content.json"
if not (SOURCE / "project.godot").is_file():
    raise SystemExit("Godot 原工程不存在；停止导入。")

data = json.loads(CONTENT.read_text(encoding="utf-8"))
chapter = {
    "quiz": data["quizzes"]["dongba"],
    "book": data["culture_books"]["dongba"],
    "completion": data["completion_pages"]["dongba"],
}
music_chapter = {
    "quiz": data["quizzes"]["music"],
    "book": data["culture_books"]["music"],
    "completion": data["completion_pages"]["music"],
}
dance_chapter = {
    "book": data["culture_books"]["dance"],
    "completion": data["completion_pages"]["dance"],
    "dance": data["dances"]["datiao_01"],
}
out = ROOT / "src" / "game" / "dongba_content.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(out.parent / "music_content.json").write_text(
    json.dumps(music_chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(out.parent / "dance_content.json").write_text(
    json.dumps(dance_chapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

dialogues = {}
for source in sorted((SOURCE / "Dialogues").glob("*.dtl")):
    events = []
    for line in source.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("[background"):
            found = re.search(r'arg="([^"]+)"', line)
            events.append({"kind": "background", "value": found.group(1) if found else ""})
        elif line.startswith("join "):
            events.append({"kind": "join", "value": line})
        elif line.startswith("leave "):
            events.append({"kind": "leave", "value": line})
        elif line.startswith("[clear"):
            events.append({"kind": "clear", "value": line})
        elif line.startswith("[wait"):
            events.append({"kind": "wait", "value": line})
        elif line.startswith("audio "):
            events.append({"kind": "audio", "value": line})
        elif ": " in line and line.split(": ", 1)[0] in ("host", "tourist"):
            speaker, text = line.split(": ", 1)
            events.append({"kind": "dialogue", "speaker": speaker, "value": text})
        else:
            events.append({"kind": "narration", "value": line})
    dialogues[source.stem] = events
(ROOT / "src" / "game" / "dialogues.json").write_text(
    json.dumps(dialogues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

assets = set()
def add(value: object) -> None:
    if isinstance(value, str) and value.startswith("res://Assets/"):
        assets.add(value.removeprefix("res://"))
    elif isinstance(value, dict):
        for item in value.values():
            add(item)
    elif isinstance(value, list):
        for item in value:
            add(item)

add(chapter)
add(music_chapter)
add(dance_chapter)
add(dialogues["opening"])
add(dialogues["clear_story"])
add(dialogues["music_intro"])
add(dialogues["dance_intro"])
add(dialogues["dance_transition"])
for event in dialogues["music_intro"]:
    if event["kind"] == "audio":
        for path in re.findall(r'res://Assets/[^\"]+', event["value"]):
            add(path)
assets.update({
    "Assets/vn/backgrounds/bg_ancient_city.png",
    "Assets/vn/portraits/char_male_casual.png",
    "Assets/vn/portraits/char_tourist_camera.png",
    "Assets/fonts/MaShanZheng-Regular.ttf",
    "Assets/dongba/sfx/sfx_correct.ogg",
    "Assets/dongba/sfx/sfx_wrong.ogg",
})
manifest = {}
for rel in sorted(assets):
    src = SOURCE / rel
    if not src.is_file():
        manifest[rel] = {"status": "missing"}
        continue
    dest = ROOT / "public" / "godot" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    manifest[rel] = {"status": "copied", "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
(ROOT / "src" / "game" / "asset_manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"Imported {sum(x['status'] == 'copied' for x in manifest.values())} unchanged assets; missing: {[k for k,v in manifest.items() if v['status'] == 'missing']}")
