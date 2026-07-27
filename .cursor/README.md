# Logit docs — Cursor workflow

This repo is part of the **logit-content** multi-repo workspace.

## How to open

1. Clone sibling repo: `marketing` (Gatsby site at logit.io)
2. In Cursor: **File → Open Workspace from File**
3. Open `marketing/logit-content.code-workspace`

That loads **marketing** and **docs-content** together.

## Skills and analytics

- Hub skill and marketing skills live in `marketing/.cursor/skills/`
- Analytics CSV exports go in `marketing/analytics/exports/`
- Invoke **`logit-content-hub`** for SEO reviews, GSC/GA4 analysis, and cross-repo edits

## Docs-specific notes

- Content: MDX under `src/pages/`
- Public URL: `https://logit.io/docs/{path}`
- Logstash filter pages: run `python3 scripts/validate-logstash-filter-docs.py` after edits
- Deploy independently from the marketing site — use a separate PR on this repo
