#!/usr/bin/env python3
"""Normalize frontmatter SEO fields and lead copy for Logstash filter pages."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "scripts/logstash-filter-inventory.json"
FILTER_DIR = ROOT / "src/pages/log-management/ingestion-pipeline/logstash-filters"

FRONTMATTER_RE = re.compile(r"^(---\n)(.*?)(\n---\n)", re.DOTALL | re.MULTILINE)

SPECIAL_DISPLAY_NAMES: dict[str, str] = {
    "elastic_integration": "Integration",
    "cidr": "CIDR",
    "csv": "CSV",
    "dns": "DNS",
    "geoip": "GeoIP",
    "http": "HTTP",
    "i18n": "i18n",
    "jdbc_streaming": "JDBC Streaming",
    "json": "JSON",
    "json_encode": "JSON Encode",
    "kv": "KV",
    "syslog_pri": "Syslog PRI",
    "tld": "TLD",
    "urldecode": "URL Decode",
    "useragent": "UserAgent",
    "uuid": "UUID",
    "xml": "XML",
}


def display_name_for(plugin: str) -> str:
    if plugin in SPECIAL_DISPLAY_NAMES:
        return SPECIAL_DISPLAY_NAMES[plugin]
    return plugin.replace("_", " ").title()


def slug_for(plugin: str) -> str:
    return plugin.replace("_", "-")


def patch_meta(text: str, meta_title: str, description: str) -> str:
    def repl(match: re.Match) -> str:
        block = match.group(2)
        lines = block.splitlines()
        out: list[str] = []
        seen_mt = False
        seen_desc = False
        for line in lines:
            if line.startswith("metaTitle:"):
                out.append(f'metaTitle: "{meta_title}"')
                seen_mt = True
            elif line.startswith("description:"):
                out.append(f'description: "{description}"')
                seen_desc = True
            else:
                out.append(line)
        if not seen_mt:
            out.append(f'metaTitle: "{meta_title}"')
        if not seen_desc:
            out.append(f'description: "{description}"')
        return match.group(1) + "\n".join(out) + match.group(3)

    return FRONTMATTER_RE.sub(repl, text, count=1)


def main() -> None:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    for entry in inventory["plugins"]:
        plugin = entry["plugin"]
        display = display_name_for(plugin)
        slug = slug_for(plugin)
        path = FILTER_DIR / f"{slug}.mdx"
        if not path.exists():
            print("skip missing", path.relative_to(ROOT))
            continue

        meta_title = f"Logstash {display} Filter Plugin | Logit.io"
        description = (
            f"{entry['summary']} Reference guide for configuring `{plugin}` in Logit.io "
            "Logstash pipelines with usage notes and examples."
        ).replace('"', '\\"')

        text = path.read_text(encoding="utf-8")
        text = patch_meta(text, meta_title, description)
        path.write_text(text, encoding="utf-8")
        print("patched", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
