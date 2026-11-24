"""
build.py — static site builder.

Content lives in content/:
  site.json        name, position, links, photo
  bio.md           short biography / research statement
  projects.json    projects and software (logo files in assets/logos/, optional)
  notice.md        optional one-line notice (empty = hidden)
  publications.bib all publications (BibTeX)

Output: _site/index.html, _site/publications.html
"""

import datetime as dt
import json
import pathlib
import re
import shutil
import struct

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

import publications

ROOT = pathlib.Path(__file__).parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
SITE = ROOT / "_site"


def md(name: str, inline: bool = False) -> Markup:
    path = CONTENT / name
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()
    if not text:
        return Markup("")
    html = markdown.markdown(text, extensions=["extra"])
    if inline:
        html = re.sub(r"^<p>(.*)</p>$", r"\1", html, flags=re.S)
    return Markup(html)


# Logos get roughly the same visual area, within a height and width cap.
LOGO_AREA = 3400      # px²
LOGO_MAX_H = 46       # px
LOGO_MAX_W = 140      # px


def image_size(path: pathlib.Path):
    head = path.read_bytes()[:4096]
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    if path.suffix.lower() == ".svg":
        txt = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', txt)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None


def logo_box(path: pathlib.Path, scale: float = 1.0):
    size = image_size(path)
    if not size or not size[1]:
        return None, None
    ratio = size[0] / size[1]
    h = min((LOGO_AREA * scale ** 2 / ratio) ** 0.5, LOGO_MAX_H * scale)
    w = h * ratio
    if w > LOGO_MAX_W:
        w, h = LOGO_MAX_W, LOGO_MAX_W / ratio
    return round(w), round(h)


def load_json(name: str):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(ASSETS, SITE / "assets")

    site = load_json("site.json")
    site["links"] = [l for l in site.get("links", []) if l.get("url")]
    if site.get("photo") and not (ROOT / site["photo"]).exists():
        site["photo"] = ""

    projects = load_json("projects.json")
    for p in projects:
        if p.get("logo") and not (ROOT / p["logo"]).exists():
            p["logo"] = ""          # falls back to the name as text
        if p.get("logo"):
            p["logo_w"], p["logo_h"] = logo_box(ROOT / p["logo"], p.get("scale", 1.0))

    pubs = publications.load()

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                      autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    ctx = {
        "site": site,
        "me": set(site.get("me", [])),
        "bio": md("bio.md"),
        "notice": md("notice.md", inline=True),
        "projects": projects,
        "pubs": pubs,
        "recent": pubs[: site.get("home_publications", 8)],
        "today": dt.date.today(),
    }
    for page in ("index.html", "publications.html"):
        (SITE / page).write_text(env.get_template(page).render(**ctx), encoding="utf-8")
        print(f"✓ {page}")
    print(f"✓ {len(pubs)} publications, {len(projects)} projects → _site/")


if __name__ == "__main__":
    main()
