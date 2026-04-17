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

## Logstash filter docs pipeline

Logstash filter pages are fully generated from two Logit-owned files and a small
chain of scripts. Nothing here reaches out to third-party documentation sites at
runtime or build time.

### Source of truth

- `scripts/logstash-filter-inventory.json` — canonical plugin catalog (ids,
  packages, coverage flags, one-line summaries).
- `scripts/logstash-filter-authored.json` — single source of truth for all
  published prose: per-plugin description, options list (name, required, type,
  default, description), and example block. Written in-house; never imported
  from third-party docs.

To add a plugin: append an entry to the inventory, add a matching entry to the
authored JSON, then re-run the generator and validator below.

To update option metadata (types/defaults): edit the authored JSON directly;
the option list is pure data and has no generator step that fetches it.

### Generate pages

```bash
python3 scripts/sync-filter-options.py
python3 scripts/apply-filter-seo.py
```

Outputs:

- `src/pages/log-management/ingestion-pipeline/logstash-filters/*.mdx`
- `src/pages/log-management/ingestion-pipeline/logstash-filters/_meta.json`
- `src/pages/log-management/ingestion-pipeline/logstash-filters.mdx`
- `src/pages/log-management/ingestion-pipeline/logstash-filters-reference.mdx`
- Updates `src/pages/log-management/ingestion-pipeline/_meta.json`

### Validate

```bash
python3 scripts/validate-logstash-filter-docs.py
```

The validator enforces structural requirements, confirms every included plugin
has an authored entry, and blocks any disallowed external hosts in generated
pages (only `logit.io` and `github.com` plugin source links are permitted).

### `apply-filter-seo.py`

Normalizes `metaTitle` and `description` in each generated filter page's
frontmatter so they follow a consistent pattern.
