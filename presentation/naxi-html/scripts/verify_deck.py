"""Focused offline structure check; no model or network calls."""
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

from build_deck import FILES, ROOT, SECTIONS


class Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name in ("src", "href"):
            if name in attrs:
                self.refs.append(attrs[name])


assert len(FILES) == 21
for number, filename in FILES.items():
    path = ROOT / filename
    html = path.read_text(encoding="utf-8")
    assert f'data-page-index="{number}"' in html, path
    assert SECTIONS[number] in html, path
    assert f"{number:02d} / 21" in html, path
    if number <= 14:
        assert f"p{number}.jpg" in html, path
    parser = Refs()
    parser.feed(html)
    for ref in parser.refs:
        if ref.startswith(("http://", "https://", "#", "data:")):
            continue
        assert (path.parent / ref).exists(), (path, ref)

diagrams = sorted((ROOT / "diagrams").glob("*.svg"))
assert len(diagrams) == 13, len(diagrams)
for path in diagrams:
    root = ET.parse(path).getroot()
    assert root.attrib["viewBox"] == "0 0 1280 430"
    assert any(path.name in (ROOT / f).read_text(encoding="utf-8") for f in FILES.values()), path

video_page = (ROOT / FILES[19]).read_text(encoding="utf-8")
assert video_page.count('data-demo-link') == 3
assert sum((ROOT / f).read_text(encoding="utf-8").count("data-evidence") for f in FILES.values()) == 19
game_page = (ROOT / FILES[7]).read_text(encoding="utf-8")
assert all(name in game_page for name in ("game-dongba-book.png", "game-music-quiz.png", "game-dance-learning.png"))
assert "courses.svg" in game_page
assert "Living Naxi" in (ROOT / FILES[1]).read_text(encoding="utf-8")
assert "制度兜底与 AI 赋能互补" in (ROOT / FILES[11]).read_text(encoding="utf-8")
assert 'show-sheet deck-closing' in (ROOT / FILES[21]).read_text(encoding="utf-8")
print("通过：21 页、6 章与尾声、13 张 SVG、19 个 4:3 截图位、3 个视频链接位及站内资源路径。")
