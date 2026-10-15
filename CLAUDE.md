# ecologyweb (Hideyuki Doi personal site)

Personal research site of Hideyuki (Hide) Doi, Biosphere Informatics Lab., Graduate School of
Informatics, Kyoto University. Published with GitHub Pages at https://hideyuki-doi.github.io/
(repo `hideyuki-doi/hideyuki-doi.github.io`). It is a personal site titled "Hideyuki Doi" ("Hide" is a nickname, kept only as a search alias in the JSON-LD), not a lab site:
do not call it "Hideyuki Doi Lab", "Hide Doi Lab" or 土居研究室.

## Structure
- `src/index.html` – all page content (Home / Research / 研究室紹介 / Members / Publications / CV), single-page app with hash routing.
- `src/themes/bold.home.html` + `src/themes/bold.css` – the active design (theme `bold`, set in `site.json`). `sidebar` and `banner` are older alternatives.
- `src/partials/` – Home research topics (`topics.html`), icons, join text.
- `src/base.css`, `src/app.js` – shared styles and behaviour (routing, search, header shrink, image fallbacks).
- `data/publications.json` – all publications. `type`: `article` (numbered 1..N by date), `japanese` (Japanese-language papers, J1..Jn, listed separately), `book`.
  `html` holds the citation: `<strong>Hideyuki Doi</strong>` bold, `<em>` for journals/species, `<sup>*</sup>` corresponding author, `†` equal contribution; add a matching note in `notes`.
  Titles in sentence case (only first word and proper nouns capitalised). DOIs shown as https://doi.org/… links.
- `data/add_dois.txt` – DOIs to add on the next build; `data/exclude_dois.txt` – DOIs never to add. No preprints.
- `assets/img/` – images. Lab photos `lab-1..4` are imported from the old Jimdo site by the workflow.
- `scripts/build.py` – builds `_site/`; `scripts/update_publications.py` – adds new papers from ORCID/Crossref; `scripts/check_links.py` – checks every DOI and image.

## Commands
- Build: `python3 scripts/build.py` → `_site/index.html`
- Local preview: `python3 -m http.server -d _site 8000`
- Single-file preview with images embedded: `python3 scripts/build.py --preview`

## Workflow
Push to `main` → GitHub Actions (`.github/workflows/site.yml`) imports images, adds new papers, builds, checks DOIs/images, deploys to Pages. It also runs every Monday 6:00 JST.

## Style
Teal from the logo (#01979a), dark network bands on every page, circular photo nodes (two per subpage, each photo used once). Keep English and Japanese text in sync (Research has an EN/日本語 switch). Check desktop and mobile widths.
