#!/usr/bin/env python3
"""Generate Logstash filter documentation pages.

Inputs:
- scripts/logstash-filter-inventory.json  — canonical plugin catalog (names, packages,
  coverage flags, short summaries).
- scripts/logstash-filter-authored.json   — single source of truth for prose:
  per-plugin description, options list (name, required, type, default, description),
  and example block. All content is written in-house by Logit.

The generator does not fetch or consume any third-party documentation at runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "scripts/logstash-filter-inventory.json"
AUTHORED_PATH = ROOT / "scripts/logstash-filter-authored.json"
INGESTION_DIR = ROOT / "src/pages/log-management/ingestion-pipeline"
FILTER_DIR = INGESTION_DIR / "logstash-filters"
FILTER_META_PATH = FILTER_DIR / "_meta.json"
HUB_PAGE_PATH = INGESTION_DIR / "logstash-filters.mdx"
REFERENCE_PAGE_PATH = INGESTION_DIR / "logstash-filters-reference.mdx"
INGESTION_META_PATH = INGESTION_DIR / "_meta.json"


SPECIAL_DISPLAY_NAMES: dict[str, str] = {
    "cidr": "CIDR",
    "csv": "CSV",
    "de_dot": "de_dot",
    "extractnumbers": "Extract Numbers",
    "geoip": "GeoIP",
    "grok": "Grok",
    "i18n": "i18n",
    "java_uuid": "Java UUID",
    "json": "JSON",
    "json_encode": "JSON Encode",
    "kv": "KV",
    "syslog_pri": "Syslog PRI",
    "threats_classifier": "Threats Classifier",
    "tld": "TLD",
    "urldecode": "URL Decode",
    "useragent": "UserAgent",
    "uuid": "UUID",
    "wurfl_device_detection": "WURFL Device Detection",
    "xml": "XML",
}

COMMON_OPTIONS: list[dict[str, str]] = [
    {
        "name": "add_field",
        "type": "hash",
        "default": "{}",
        "description": "Adds fields when the filter succeeds. Supports dynamic field names and values.",
        "example": 'add_field => { "pipeline_stage" => "parsed" }',
    },
    {
        "name": "add_tag",
        "type": "array",
        "default": "[]",
        "description": "Adds one or more tags when the filter succeeds.",
        "example": 'add_tag => ["parsed", "logstash_filter"]',
    },
    {
        "name": "enable_metric",
        "type": "boolean",
        "default": "true",
        "description": "Enables or disables metric collection for this plugin instance.",
        "example": "enable_metric => true",
    },
    {
        "name": "id",
        "type": "string",
        "default": "none",
        "description": "Sets an explicit plugin instance ID for monitoring and troubleshooting.",
        "example": 'id => "my_filter_instance"',
    },
    {
        "name": "periodic_flush",
        "type": "boolean",
        "default": "false",
        "description": "Calls the filter flush method at regular intervals.",
        "example": "periodic_flush => false",
    },
    {
        "name": "remove_field",
        "type": "array",
        "default": "[]",
        "description": "Removes fields when the filter succeeds. Supports dynamic field names.",
        "example": 'remove_field => ["tmp_field"]',
    },
    {
        "name": "remove_tag",
        "type": "array",
        "default": "[]",
        "description": "Removes tags when the filter succeeds.",
        "example": 'remove_tag => ["temporary"]',
    },
]

PLUGIN_USE_CASES: dict[str, list[str]] = {
    "grok": [
        "Parse unstructured log lines into structured fields for dashboards and alerts.",
        "Extract reusable fields (for example request method, path, and status code) from message text.",
    ],
    "json": [
        "Decode JSON payloads stored in `message` or another source field.",
        "Promote parsed JSON fields into searchable OpenSearch document fields.",
    ],
    "mutate": [
        "Rename, convert, and normalize fields before indexing.",
        "Clean noisy event payloads by removing temporary or unused fields.",
    ],
    "geoip": [
        "Enrich IP fields with geo and ASN metadata for geolocation dashboards.",
        "Support country/region-based filtering and alert routing workflows.",
    ],
    "kv": [
        "Parse key=value log messages into discrete fields.",
        "Handle dynamic key/value payloads from app and infrastructure logs.",
    ],
    "ruby": [
        "Apply custom transformations not covered by built-in filters.",
        "Implement edge-case parsing logic directly in pipeline code.",
    ],
}

PLUGIN_IO_NOTES: dict[str, str] = {
    "grok": "Parses text patterns and writes named captures into event fields.",
    "json": "Parses JSON from an input field and writes decoded keys to root or `target`.",
    "csv": "Splits delimited text into columns and writes them as fields.",
    "kv": "Parses key=value strings and emits dynamic fields from those pairs.",
    "date": "Parses date/time strings and updates timestamp fields.",
    "geoip": "Uses an IP/hostname input to enrich events with location and network metadata.",
    "mutate": "Applies in-place field mutations such as rename, convert, replace, and remove.",
    "dissect": "Tokenizes text by delimiters and writes deterministic captures to fields.",
    "ruby": "Executes custom Ruby logic against each event for advanced transformations.",
    "split": "Creates multiple events from one field value (array or split string).",
    "aggregate": "Correlates events by task key and emits aggregate state on completion/timeout.",
    "elapsed": "Tracks paired start/end events and outputs elapsed timing details.",
    "translate": "Maps input values through a dictionary into normalized output values.",
}

SUPPORT_APPROVAL_NOTES: dict[str, str] = {
    "ruby": "Use of the `ruby` filter requires prior approval from Logit.io Support before enabling it in production pipelines.",
}

# Plugins skipped from hosted docs because their only useful modes require reaching
# external services from the hosted pipeline runtime. These plugin ids must match
# inventory entries exactly.
EXCLUDED_PLUGINS: set[str] = {
    "dns",
    "elastic_integration",
    "elasticsearch",
    "http",
    "jdbc_streaming",
    "memcached",
}


def load_inventory() -> dict:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def load_authored() -> dict[str, dict]:
    if not AUTHORED_PATH.exists():
        return {}
    data = json.loads(AUTHORED_PATH.read_text(encoding="utf-8"))
    return data.get("plugins", {}) or {}


def slug_for(plugin: str) -> str:
    return plugin.replace("_", "-")


def display_name_for(plugin: str) -> str:
    if plugin in SPECIAL_DISPLAY_NAMES:
        return SPECIAL_DISPLAY_NAMES[plugin]
    return plugin.replace("_", " ").title()


def render_installation_scope(entry: dict) -> str:
    scope: list[str] = []
    if entry.get("defaultBundled"):
        scope.append("default/bundled")
    if entry.get("imageInstalled"):
        scope.append("explicitly installed in the Logit image")
    if not scope:
        scope.append("custom")
    return ", ".join(scope)


def _strip_code_fence(value: str | None) -> str:
    if not value:
        return ""
    text = value.strip()
    while len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    return text


def _find_option(authored: dict | None, option_name: str) -> dict | None:
    if not authored:
        return None
    for item in authored.get("options") or []:
        if item.get("name") == option_name:
            return item
    return None


def _option_names(authored: dict | None) -> list[str]:
    if not authored:
        return []
    return [item.get("name", "") for item in (authored.get("options") or []) if item.get("name")]


def _render_option_bullet(option: dict) -> str:
    name = option.get("name", "unknown")
    option_type = (option.get("type") or "").strip()
    default_value = (option.get("default") or "").strip()
    description = (option.get("description") or "").strip()

    bits: list[str] = []
    if option_type:
        bits.append(f"type: {option_type}")
    if default_value:
        bits.append(f"default: {default_value}")
    suffix = f" ({'; '.join(bits)})" if bits else ""
    desc = f" — {description}" if description else ""
    return f"- `{name}`{suffix}{desc}"


def _best_option_names(authored: dict | None) -> list[str]:
    names = _option_names(authored)
    priority = [
        "source",
        "field",
        "target",
        "code",
        "task_id",
        "match",
        "dictionary_path",
        "pattern",
        "tag_on_failure",
    ]
    selected: list[str] = []
    for key in priority:
        if key in names and key not in selected:
            selected.append(key)
    for key in names:
        if key not in selected:
            selected.append(key)
        if len(selected) >= 4:
            break
    return selected[:4]


def _infer_use_cases(plugin: str, summary: str, authored: dict | None) -> list[str]:
    summary_l = summary.lower()
    option_names = _option_names(authored)

    inferred: list[str] = []
    if "parse" in summary_l:
        inferred.append("Parse incoming log payloads into structured fields for querying and dashboards.")
    if "enrich" in summary_l or "lookup" in summary_l:
        inferred.append("Enrich events with contextual data to support routing and correlation.")
    if "aggregate" in summary_l:
        inferred.append("Correlate multiple related events into task/session-level outputs.")
    if "uuid" in summary_l:
        inferred.append("Attach stable identifiers to events for deduplication and traceability.")
    if "ruby" in plugin:
        inferred.append("Apply custom transformation logic when built-in filters are not sufficient.")
    if "tag_on_failure" in option_names:
        inferred.append("Tag failed operations and route them to dedicated troubleshooting views.")

    if len(inferred) < 2:
        inferred.append("Transform fields before indexing to keep schema and naming consistent.")
    if len(inferred) < 2:
        inferred.append("Prepare high-quality fields for alerts, dashboards, and downstream pipelines.")
    return inferred[:2]


def _infer_flow_line(authored: dict | None) -> str:
    option_names = _option_names(authored)
    if "source" in option_names and "target" in option_names:
        return "Flow: reads a configured source field and writes parsed/transformed output into a target or root fields."
    if "field" in option_names:
        return "Flow: reads one or more configured fields, applies plugin logic, then updates event fields in place."
    if "task_id" in option_names:
        return "Flow: correlates events using a task identifier and emits aggregate state on completion/timeout."
    return "Flow: processes matching events and mutates fields/tags within the same event."


def _render_plugin_overview_section(plugin: str, summary: str, authored: dict | None) -> list[str]:
    summary_sentence = summary.strip() or "Processes events in Logstash."
    if summary_sentence:
        summary_sentence = summary_sentence[0].upper() + summary_sentence[1:]

    lines: list[str] = [
        "## Plugin overview",
        "",
        f"`{plugin}` is used in the Logstash filter stage. {summary_sentence}",
        "",
    ]

    use_cases = PLUGIN_USE_CASES.get(plugin) or _infer_use_cases(plugin, summary, authored)
    lines.append("### Typical use cases")
    lines.append("")
    for item in use_cases:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("### Input and output behavior")
    lines.append("")

    source_opt = _find_option(authored, "source") or _find_option(authored, "field")
    target_opt = _find_option(authored, "target")
    failure_opt = _find_option(authored, "tag_on_failure")
    io_note = PLUGIN_IO_NOTES.get(plugin)
    key_options = _best_option_names(authored)

    if io_note:
        lines.append(f"- Flow: {io_note}")
    else:
        lines.append(f"- {_infer_flow_line(authored)}")

    if source_opt:
        default_source = _strip_code_fence(source_opt.get("default"))
        suffix = f" (default: `{default_source}`)" if default_source and default_source != "none" else ""
        lines.append(f"- Input field: `{source_opt.get('name')}`{suffix}.")
    else:
        lines.append("- Input: works on events that match your surrounding `if` conditions.")

    if target_opt:
        default_target = _strip_code_fence(target_opt.get("default"))
        if default_target and default_target != "none":
            lines.append(f"- Output target: `{target_opt.get('name')}` (default: `{default_target}`).")
        else:
            lines.append(f"- Output target: controlled by `{target_opt.get('name')}`.")
    else:
        lines.append("- Output: updates the current event in place unless configured otherwise.")

    if key_options:
        lines.append("- Important options: " + ", ".join(f"`{name}`" for name in key_options) + ".")

    if failure_opt:
        default_failure = (failure_opt.get("default") or "").strip()
        lines.append(
            "- Failure signaling: uses `tag_on_failure`"
            + (f" (default: {default_failure})" if default_failure else "")
            + " so failed events can be routed or inspected."
        )

    lines.append("")
    return lines


def _render_options_sections(authored: dict | None) -> list[str]:
    options = list((authored or {}).get("options") or [])
    if not options:
        return [
            "### Required",
            "",
            "- No required plugin-specific options are defined.",
            "",
            "### Optional",
            "",
            "- This plugin has no plugin-specific options; use the shared filter options documented below.",
            "",
        ]

    required = [option for option in options if option.get("required")]
    optional = [option for option in options if not option.get("required")]

    lines: list[str] = ["### Required", ""]
    if required:
        lines.extend(_render_option_bullet(option) for option in required)
    else:
        lines.append("- No required plugin-specific options.")
    lines.extend(["", "### Optional", ""])
    if optional:
        lines.extend(_render_option_bullet(option) for option in optional)
    else:
        lines.append("- No optional plugin-specific options.")
    lines.append("")
    return lines


def _render_example(plugin: str, authored: dict | None) -> list[str]:
    baseline = "\n".join(
        [
            "filter {",
            f"  {plugin} {{",
            "    # Configure plugin options here",
            "  }",
            "}",
        ]
    )
    code = baseline
    example = (authored or {}).get("example")
    if isinstance(example, str) and example.strip():
        candidate = example.replace("```", "").rstrip()
        if f"{plugin} " in candidate or f"{plugin}{{" in candidate:
            code = candidate
    return ["```ruby copy", *code.splitlines(), "```"]


def _render_common_options_section(plugin: str) -> list[str]:
    lines: list[str] = [
        "## Common options configuration",
        "",
        "All Logstash filter plugins support these shared options:",
        "",
    ]
    for item in COMMON_OPTIONS:
        lines.append(
            f"- `{item['name']}` (type: {item['type']}; default: `{item['default']}`) — {item['description']}"
        )
    lines.extend(
        [
            "",
            "```ruby copy",
            "filter {",
            f"  {plugin} {{",
        ]
    )
    for item in COMMON_OPTIONS:
        lines.append(f"    {item['example']}")
    lines.extend(
        [
            "  }",
            "}",
            "```",
            "",
        ]
    )
    return lines


def _render_logit_workflow_section(plugin: str) -> list[str]:
    return [
        "## Apply in Logit.io",
        "",
        "1. Open your stack in Logit.io and navigate to **Logstash Pipelines**.",
        f"2. In the `filter {{ ... }}` section, add a `{plugin}` block.",
        "3. Save your pipeline changes, then restart the Logstash pipeline if prompted.",
        "4. Send sample events and verify parsed/enriched fields in OpenSearch Dashboards.",
        "",
    ]


def _render_validation_section(plugin: str) -> list[str]:
    return [
        "## Validation checklist",
        "",
        f"- Confirm the `{plugin}` block compiles without syntax errors.",
        "- Verify expected new/updated fields exist in sample documents.",
        "- Verify unexpected fields are not removed unless explicitly configured.",
        "- Confirm tags added on success/failure align with your alerting and routing rules.",
        "",
    ]


def _render_troubleshooting_section(plugin: str, authored: dict | None) -> list[str]:
    lines: list[str] = [
        "## Troubleshooting",
        "",
        "- If events are unchanged, verify your filter condition (`if ...`) matches incoming events.",
        "- If the pipeline fails to start, validate braces/quotes and retry with a minimal filter block.",
    ]

    failure_opt = _find_option(authored, "tag_on_failure")
    if failure_opt:
        default_value = (failure_opt.get("default") or "").strip() or "plugin default"
        lines.append(f"- Check for `tag_on_failure` tags (default: {default_value}) to quickly isolate parse/mutation failures.")

    exception_opt = _find_option(authored, "tag_on_exception")
    if exception_opt:
        default_value = (exception_opt.get("default") or "").strip() or "plugin default"
        lines.append(f"- Check for `tag_on_exception` tags (default: {default_value}) when plugin code throws runtime exceptions.")

    lines.extend(
        [
            "- If throughput drops, reduce expensive operations and test with representative sample volume.",
            "",
        ]
    )
    return lines


def render_plugin_page(entry: dict, authored: dict | None) -> str:
    plugin = entry["plugin"]
    display = display_name_for(plugin)
    package = entry["package"]
    scope = render_installation_scope(entry)
    summary = entry["summary"]
    github_url = f"https://github.com/logstash-plugins/{package}" if package.startswith("logstash-filter-") else None
    if plugin == "math":
        github_url = "https://github.com/robin13/logstash-filter-math"

    authored_description = ""
    if authored and isinstance(authored.get("description"), str):
        authored_description = authored["description"].strip()
    lead_paragraph = authored_description or f"The `{plugin}` filter plugin {summary.lower()}"

    lines: list[str] = [
        "---",
        f'title: "Logstash Filter: {display}"',
        f'metaTitle: "Logstash {display} Filter Plugin Reference"',
        f'description: "{summary} Includes usage guidance, configuration options, validation steps, and troubleshooting for the {plugin} filter plugin on Logit.io."',
        "stackTypes: logs",
        "---",
        "",
        f"# {display} filter plugin",
        "",
        lead_paragraph,
        "",
        f"- Package: `{package}`",
        f"- Coverage source: {scope}",
        f"- Official catalog entry: {'Yes' if entry.get('official', False) else 'No'}",
        "",
    ]

    approval_note = SUPPORT_APPROVAL_NOTES.get(plugin)
    if approval_note:
        lines.extend(
            [
                "<Callout type=\"warning\">",
                approval_note,
                "</Callout>",
                "",
            ]
        )

    lines.extend(
        [
            *_render_plugin_overview_section(plugin, summary, authored),
            "## Options",
            "",
            *_render_options_sections(authored),
            "## Example configuration",
            "",
            *_render_example(plugin, authored),
            "",
            *_render_common_options_section(plugin),
            *_render_logit_workflow_section(plugin),
            *_render_validation_section(plugin),
            *_render_troubleshooting_section(plugin, authored),
            "## References",
            "",
        ]
    )
    if github_url:
        lines.append(f"- GitHub package: [`{package}`]({github_url})")
    lines.append("- Canonical catalog: [/log-management/ingestion-pipeline/logstash-filters-reference](/log-management/ingestion-pipeline/logstash-filters-reference)")
    lines.append("")
    return "\n".join(lines)


def render_hub_page(total_plugins: int) -> str:
    return "\n".join(
        [
            "---",
            "title: Logstash Filters",
            'metaTitle: "Logstash Filter Plugins Reference | Logit.io"',
            'description: "Browse Logstash filter plugin references for the filters available in Logit.io, including default/bundled and image-installed filters."',
            "pagination: false",
            "timestamp: false",
            "stackTypes: logs",
            "---",
            "",
            "# Logstash Filters",
            "",
            f"This section contains reference pages for `{total_plugins}` Logstash filter plugins available to Logit.io users.",
            "",
            "Coverage follows the canonical inventory in `scripts/logstash-filter-inventory.json` and includes:",
            "",
            "- Default/bundled filters in Logstash",
            "- Additional filters explicitly installed in the Logit image",
            "- Excludes plugins that require direct external connectivity from hosted pipeline runtime",
            "",
            "<FolderBrowser />",
            "",
        ]
    )


def render_reference_page(entries: list[dict], excluded_entries: list[dict]) -> str:
    lines: list[str] = [
        "---",
        "title: Logstash Filters Reference",
        'metaTitle: "Canonical Logstash Filters Inventory | Logit.io"',
        'description: "Canonical inventory and coverage matrix for Logstash filter plugins documented by Logit.io."',
        "stackTypes: logs",
        "---",
        "",
        "# Logstash Filters Reference",
        "",
        "This page is generated from the canonical inventory at `scripts/logstash-filter-inventory.json`.",
        "",
        "## Coverage matrix",
        "",
        "| Plugin | Package | Official | Default/Bundled | Image-installed | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        plugin = entry["plugin"]
        package = entry["package"]
        official = "Yes" if entry["official"] else "No"
        default_bundled = "Yes" if entry["defaultBundled"] else "No"
        image_installed = "Yes" if entry["imageInstalled"] else "No"
        status = entry["status"]
        lines.append(f"| `{plugin}` | `{package}` | {official} | {default_bundled} | {image_installed} | `{status}` |")

    lines.extend(["", "## Plugin details", ""])

    for entry in entries:
        plugin = entry["plugin"]
        display = display_name_for(plugin)
        slug = slug_for(plugin)
        lines.extend(
            [
                f"#### {display} (`{plugin}`)",
                f"- Package: `{entry['package']}`",
                f"- Summary: {entry['summary']}",
                f"- Coverage status: `{entry['status']}`",
                f"- Docs page: [/log-management/ingestion-pipeline/logstash-filters/{slug}](/log-management/ingestion-pipeline/logstash-filters/{slug})",
                "",
            ]
        )

    if excluded_entries:
        lines.extend(["## Excluded from hosted docs", ""])
        lines.append(
            "The following plugins are intentionally excluded from this hosted docs set because they require direct external connectivity from pipeline runtime."
        )
        lines.append("")
        lines.append("| Plugin | Package | Reason |")
        lines.append("| --- | --- | --- |")
        for entry in excluded_entries:
            lines.append(
                f"| `{entry['plugin']}` | `{entry['package']}` | Requires external host/service connectivity |"
            )
        lines.append("")

    return "\n".join(lines)


DEFAULT_INGESTION_MENU: list[tuple[str, str]] = [
    ("overview", "Overview"),
    ("configuration", "Configuration"),
    ("adding-inputs", "Adding Inputs"),
    ("api-key-logstash", "API Key for Logstash"),
    ("differentiate-log-types-logstash", "Differentiating Log Types"),
    ("logstash-filters", "Logstash Filters"),
    ("logstash-filters-reference", "Logstash Filters Reference"),
    ("remove-fields-logstash-filters", "Removing Fields with Filters"),
    ("change-index-names-from-logstash", "Changing Index Names"),
    ("logstash-dead-letter-queue", "Dead Letter Queue (DLQ)"),
]


def update_ingestion_meta() -> None:
    existing: dict[str, str] = {}
    if INGESTION_META_PATH.exists():
        existing = json.loads(INGESTION_META_PATH.read_text(encoding="utf-8"))

    ordered: dict[str, str] = {}
    for key, default_label in DEFAULT_INGESTION_MENU:
        ordered[key] = existing.get(key, default_label)

    for key, value in existing.items():
        if key not in ordered:
            ordered[key] = value

    INGESTION_META_PATH.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    inventory = load_inventory()
    authored = load_authored()
    all_entries = sorted(inventory["plugins"], key=lambda item: item["plugin"])
    included_entries: list[dict] = [entry for entry in all_entries if entry["plugin"] not in EXCLUDED_PLUGINS]
    excluded_entries: list[dict] = [entry for entry in all_entries if entry["plugin"] in EXCLUDED_PLUGINS]

    FILTER_DIR.mkdir(parents=True, exist_ok=True)

    missing_authored: list[str] = []
    filter_meta: dict[str, str] = {}
    generated_files: set[str] = set()
    for entry in included_entries:
        plugin = entry["plugin"]
        slug = slug_for(plugin)
        display = display_name_for(plugin)
        filter_meta[slug] = display
        page_path = FILTER_DIR / f"{slug}.mdx"
        plugin_authored = authored.get(plugin)
        if not plugin_authored:
            missing_authored.append(plugin)
        page_path.write_text(render_plugin_page(entry, plugin_authored), encoding="utf-8")
        generated_files.add(page_path.name)
        print("generated", page_path.relative_to(ROOT))

    if missing_authored:
        print("warning: missing authored content for plugins:", ", ".join(missing_authored))

    for page_path in FILTER_DIR.glob("*.mdx"):
        if page_path.name in {"_meta.json"}:
            continue
        if page_path.name not in generated_files:
            page_path.unlink(missing_ok=True)
            print("removed", page_path.relative_to(ROOT))

    FILTER_META_PATH.write_text(json.dumps(filter_meta, indent=2) + "\n", encoding="utf-8")
    HUB_PAGE_PATH.write_text(render_hub_page(len(included_entries)), encoding="utf-8")
    REFERENCE_PAGE_PATH.write_text(render_reference_page(included_entries, excluded_entries), encoding="utf-8")
    update_ingestion_meta()
    print("updated", FILTER_META_PATH.relative_to(ROOT))
    print("updated", HUB_PAGE_PATH.relative_to(ROOT))
    print("updated", REFERENCE_PAGE_PATH.relative_to(ROOT))
    print("updated", INGESTION_META_PATH.relative_to(ROOT))


if __name__ == "__main__":
    main()
