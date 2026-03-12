"""
build.py — Static site builder for enrico.daga.net
Reads content from content/, renders via Jinja2 templates, writes to _site/.
"""

import json
import shutil
import pathlib
import markdown
import bibtexparser
from typing import Union, Dict, List
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from jinja2 import Environment, FileSystemLoader

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT     = pathlib.Path(__file__).parent
CONTENT  = ROOT / "content"
TEMPLATES= ROOT / "templates"
ASSETS   = ROOT / "assets"
SITE     = ROOT / "_site"

# ── Helpers ────────────────────────────────────────────────────────────────

def read_md(filename: str) -> str:
    """Render a Markdown file from content/ to an HTML string."""
    path = CONTENT / filename
    if not path.exists():
        return ""
    return markdown.markdown(path.read_text(encoding="utf-8"), extensions=["extra"])


def load_json(filename: str) -> Union[list, dict]:
    """Load a JSON file from content/."""
    path = CONTENT / filename
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def parse_bib(filename: str = "publications.bib") -> Dict[str, List]:
    """
    Parse a BibTeX file and return a dict keyed by entry type,
    each value being a list of entries sorted by year descending.
    """
    path = CONTENT / filename
    if not path.exists():
        return {}

    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    with path.open(encoding="utf-8") as f:
        bib_db = bibtexparser.load(f, parser=parser)

    # Group by ENTRYTYPE
    groups: Dict[str, List] = {}
    for entry in bib_db.entries:
        etype = entry.get("ENTRYTYPE", "misc").lower()
        groups.setdefault(etype, []).append(entry)

    # Sort each group by year descending
    for etype in groups:
        groups[etype].sort(key=lambda e: int(e.get("year", 0)), reverse=True)

    return groups


# Canonical display order and labels for publication types
PUB_TYPE_ORDER = [
    ("article",       "Journal Articles"),
    ("inproceedings", "Conference Papers"),
    ("incollection",  "Book Chapters"),
    ("proceedings",   "Edited Proceedings"),
    ("misc",          "Edited Special Issues / Other"),
    ("phdthesis",     "PhD Thesis"),
]

# ── Build ──────────────────────────────────────────────────────────────────

def clean():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    print("✓ Cleaned _site/")


def copy_assets():
    dest = SITE / "assets"
    shutil.copytree(ASSETS, dest)
    print("✓ Copied assets/")


def build_pages(env: Environment):
    bib_groups = parse_bib()
    pub_sections = [
        (label, bib_groups.get(etype, []))
        for etype, label in PUB_TYPE_ORDER
        if bib_groups.get(etype)
    ]

    pages = {
        "index.html": {
            "title": "Enrico Daga — Senior Research Fellow, The Open University",
            "description": "Personal academic website of Enrico Daga, Senior Research Fellow at the Knowledge Media Institute, The Open University.",
            "projects":  load_json("projects.json"),
            "talks":     load_json("talks.json")[:5],   # latest 5 for homepage
            "tools":     load_json("tools.json"),
            "bib_groups": bib_groups,
        },
        "about.html": {
            "title": "About — Enrico Daga",
            "description": "Biography and background of Enrico Daga.",
            "content": read_md("about.md"),
        },
        "research.html": {
            "title": "Research — Enrico Daga",
            "description": "Research interests, projects, and software tools.",
            "interests":   read_md("research-interests.md"),
            "projects":    load_json("projects.json"),
            "tools":       load_json("tools.json"),
            "bib_groups":  bib_groups,
        },
        "publications.html": {
            "title": "Publications — Enrico Daga",
            "description": "Full list of peer-reviewed publications by Enrico Daga.",
            "pub_sections": pub_sections,
        },
        "teaching.html": {
            "title": "Teaching & Supervision — Enrico Daga",
            "description": "Teaching activities and PhD supervision.",
            "teaching":    read_md("teaching.md"),
            "supervision": read_md("supervision.md"),
        },
        "service.html": {
            "title": "Service & Community — Enrico Daga",
            "description": "Invited talks, academic service, and community roles.",
            "service":  read_md("service.md"),
            "talks":    load_json("talks.json"),
        },
        "contact.html": {
            "title": "Contact — Enrico Daga",
            "description": "Contact information and collaboration enquiries.",
            "content": read_md("contact.md"),
        },
    }

    for filename, ctx in pages.items():
        tmpl = env.get_template(filename)
        html = tmpl.render(**ctx)
        (SITE / filename).write_text(html, encoding="utf-8")
        print(f"✓ Built {filename}")


def main():
    clean()
    copy_assets()
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)
    build_pages(env)
    print("\n✅ Site built → _site/")


if __name__ == "__main__":
    main()
