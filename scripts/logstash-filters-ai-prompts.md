# Logstash Filters AI Prompt Pack

Use these prompts to run the Logstash Filters documentation workflow consistently.

## 1) Master Orchestration Prompt

```text
You are updating docs in the docs-content repository.

Goal:
- Refresh Logstash filter docs using the canonical inventory and generation scripts.

Mandatory scope:
- Logstash filters only.
- Include all plugins in scripts/logstash-filter-inventory.json.
- Do not change non-filter docs unless link fixes require it.

Sources of truth (Logit-owned, no third-party imports):
- scripts/logstash-filter-inventory.json — plugin catalog.
- scripts/logstash-filter-authored.json — per-plugin description, options list
  (name, required, type, default, description), and example block.

Tasks:
1. Validate inventory and authored JSON for valid JSON and required fields.
2. Run:
   - python3 scripts/sync-filter-options.py
   - python3 scripts/apply-filter-seo.py
   - python3 scripts/validate-logstash-filter-docs.py
3. Verify:
   - each included plugin has a page in src/pages/log-management/ingestion-pipeline/logstash-filters/
   - _meta.json includes every generated page slug
   - ingestion-pipeline/_meta.json contains logstash-filters entries
4. Produce a concise report:
   - files changed
   - plugin count covered
   - QA issues (if any)

Constraints:
- Keep generated sections deterministic.
- Keep language concise and technical.
- No placeholders like "TODO" in published docs.
- All descriptions and example blocks must be written in-house and live in the
  authored JSON. Do not fetch or paste content from third-party documentation.
```

## 2) Per-filter Page Prompt

```text
Update one Logstash filter doc page:
- Target plugin: <PLUGIN_ID>
- Target file: src/pages/log-management/ingestion-pipeline/logstash-filters/<PLUGIN_SLUG>.mdx

Requirements:
- Keep frontmatter valid.
- Keep sections:
  - ## Options
  - ## Example configuration
  - ## References
- Preserve generated-style consistency with sibling pages.
- Ensure package name, summary, and links match scripts/logstash-filter-inventory.json.
- Keep examples syntactically valid Logstash config.

Return:
- Brief summary of changes
- Any unresolved technical ambiguity
```

## 3) Canonical Inventory / Authored Content Update Prompt

```text
Update scripts/logstash-filter-inventory.json and/or
scripts/logstash-filter-authored.json.

Inventory requirements:
- Keep valid JSON.
- For each plugin include:
  - plugin
  - package
  - official (bool)
  - defaultBundled (bool)
  - imageInstalled (bool)
  - status
  - summary
- Do not remove existing plugins unless explicitly requested.
- Preserve alphabetical ordering by plugin in output.

Authored content requirements:
- Keep valid JSON.
- Every included plugin must have a plugins.<plugin> entry with:
  - description (Logit-written, 1-3 sentences)
  - options: ordered list of { name, required, type, default, description }
  - example: Logit-written filter block as a single string
- All prose and examples must be written in-house. Do not paste from third-party
  documentation (Elastic docs, plugin READMEs, etc.).

After update:
- Run python3 scripts/sync-filter-options.py
- Run python3 scripts/apply-filter-seo.py
- Run python3 scripts/validate-logstash-filter-docs.py
- Report plugin count delta and list added/removed plugin IDs.
```

## 4) QA Prompt

```text
Perform QA for generated Logstash filter docs only.

Scope:
- src/pages/log-management/ingestion-pipeline/logstash-filters/
- src/pages/log-management/ingestion-pipeline/logstash-filters-reference.mdx
- src/pages/log-management/ingestion-pipeline/logstash-filters.mdx

Checks:
1. Every filter page has frontmatter + H1 + Options + Example configuration + References.
2. Every page includes a code block with a valid `filter { <plugin> { ... } }` shape.
3. _meta.json keys map to existing files.
4. Reference page contains all inventory plugins.
5. No empty bullet points, dangling callouts, or malformed markdown tables.

Output:
- Findings by severity (high/medium/low)
- File paths for each finding
- Suggested minimal fix for each issue
```
