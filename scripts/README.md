# Scripts

## `sync-destination-options.py`

Regenerates the **Options** section on each alerting destination page from the canonical full reference (`src/pages/log-management/alerting/alert-reference.mdx`, `####` alerter headings).

### What it does

- Reads `src/pages/log-management/alerting/alert-reference.mdx`.
- For each mapped alerter (see `SECTION_FILE` in the script), rebuilds **Required** / **Optional** bullets and attaches example YAML from the reference under the relevant keys.
- Writes into `src/pages/log-management/alerting/destinations/*.mdx`, replacing everything from `## Options` through the line before `## Full working example` (or `## Example rule`). The **Full working example** block at the bottom of each page is left as-is.
- Removes a legacy `## Example snippets` block if present.

### Requirements

- **Python 3.10+** (uses `list[str]` / `str | None` style annotations).
- No third-party packages—stdlib only.

### How to run

From anywhere (paths are resolved from the repo root via the script location):

```bash
python3 scripts/sync-destination-options.py
```

Or:

```bash
cd /path/to/docs-content
./scripts/sync-destination-options.py
```

Ensure the script stays executable if you use `./` (`chmod +x scripts/sync-destination-options.py`).

### Before / after

- **Review with git** before committing: `git diff src/pages/log-management/alerting/destinations/`
- If a destination file is missing, or its structure does not include `## Options` and `## Full working example` (or `## Example rule`), the script prints `skip …` for that file and does not update it.
- New alerters in the reference need a new entry in `SECTION_FILE` and a matching `destinations/<slug>.mdx` page with the expected headings.

### Related

- `apply-destination-seo.py` — front matter / titles for destination pages.
- `apply-rule-type-seo.py` — rule-type hub SEO.
