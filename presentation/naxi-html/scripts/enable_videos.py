"""Apply configured HTTPS demonstration links to the application slide.

An empty URL remains a labelled pending state. No video is embedded or fetched.
"""
from pathlib import Path
import re

from build_deck import ROOT, demo_link

PAGE = ROOT / "slides" / "19-application.html"
SLOT = re.compile(
    r'<(?:a|span) class="demo-link(?: pending)?" data-demo-link '
    r'data-demo-key="(dongba|music|dance)"[^>]*>.*?</(?:a|span)>'
)


def main() -> None:
    html = PAGE.read_text(encoding="utf-8")
    found = []

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        found.append(key)
        return demo_link(key)

    updated = SLOT.sub(replace, html)
    if sorted(found) != ["dance", "dongba", "music"]:
        raise ValueError(f"演示链接位不完整：{found}")
    if updated != html:
        PAGE.write_text(updated, encoding="utf-8")
    print("视频链接位 3 个；真实 HTTPS 链接已按 links.json 更新，空链接保持待添加。")


if __name__ == "__main__":
    main()
