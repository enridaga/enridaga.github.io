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
from highlights import select_highlights

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


def get_type_label(entry: dict) -> str:
    """
    Map a BibTeX entry to one of three display categories:
      Journal     — @article
      Conference  — @inproceedings
      Other       — everything else (workshop papers, book chapters, edited
                    proceedings, special issues, abstracts, posters, demos,
                    thesis, misc, etc.)
    """
    etype = entry.get("ENTRYTYPE", "misc").lower()
    if etype == "article":
        return "Journal"
    if etype == "inproceedings":
        return "Conference"
    return "Other"


def parse_bib(filename: str = "publications.bib") -> Dict:
    """
    Parse a BibTeX file and return:
      - 'all':    flat list of all entries sorted by year descending
      - 'groups': dict keyed by ENTRYTYPE, each a list sorted by year descending
    Each entry is augmented with:
      - 'type_label':     one of Journal / Conference / Other
      - 'is_featured':    bool from featured = {true} field
      - 'is_under_review': bool from status = {under review} field
    """
    path = CONTENT / filename
    if not path.exists():
        return {"all": [], "groups": {}}

    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    with path.open(encoding="utf-8") as f:
        bib_db = bibtexparser.load(f, parser=parser)

    entries = []
    for entry in bib_db.entries:
        entry["type_label"]      = get_type_label(entry)
        entry["is_featured"]     = entry.get("featured", "").strip().lower() == "true"
        status = entry.get("status", "").strip().lower()
        entry["is_under_review"] = status == "under review"
        entry["is_accepted"]     = status == "accepted"
        entries.append(entry)

    # Flat list sorted by year descending
    all_sorted = sorted(entries, key=lambda e: int(e.get("year", 0)), reverse=True)

    # Grouped by ENTRYTYPE, each group sorted by year descending
    groups: Dict[str, List] = {}
    for entry in entries:
        etype = entry.get("ENTRYTYPE", "misc").lower()
        groups.setdefault(etype, []).append(entry)
    for etype in groups:
        groups[etype].sort(key=lambda e: int(e.get("year", 0)), reverse=True)

    return {"all": all_sorted, "groups": groups}


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
    bib = parse_bib()

    pages = {
        "index.html": {
            "title": "Enrico Daga — Senior Research Fellow, The Open University",
            "description": "Personal academic website of Enrico Daga, Senior Research Fellow at the Knowledge Media Institute, The Open University.",
            "projects":   load_json("projects.json"),
            "talks":      select_highlights(load_json("talks.json")),
            "tools":      load_json("tools.json"),
            "bib_groups": bib["groups"],
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
            "bib_groups":  bib["groups"],
        },
        "publications.html": {
            "title": "Publications — Enrico Daga",
            "description": "Full list of peer-reviewed publications by Enrico Daga.",
            "publications": bib["all"],
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
