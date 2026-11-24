# enridaga/website

Static personal site. `python build.py` writes `_site/`; GitHub Actions builds and deploys on every push.

## What to edit

| File | Content |
|---|---|
| `content/site.json` | name, position, links, photo |
| `content/bio.md` | short biography and roles |
| `content/projects.json` | projects and software; logos go in `assets/logos/` (if the file is missing, the name is shown) |
| `content/notice.md` | optional one-line notice; empty = hidden |

## Publications

All in `content/publications.bib` (e.g. exported from Google Scholar or DBLP). Optional field: `status = {under review}` or `{accepted}`.
`python publications.py` prints the list as the site shows it.

## Local preview

    ./local.sh
