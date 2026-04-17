#!/usr/bin/env python3
"""QA checks for generated Logstash filter docs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "scripts/logstash-filter-inventory.json"
AUTHORED_PATH = ROOT / "scripts/logstash-filter-authored.json"
FILTER_DIR = ROOT / "src/pages/log-management/ingestion-pipeline/logstash-filters"
FILTER_META_PATH = FILTER_DIR / "_meta.json"
REFERENCE_PATH = ROOT / "src/pages/log-management/ingestion-pipeline/logstash-filters-reference.mdx"
HUB_PATH = ROOT / "src/pages/log-management/ingestion-pipeline/logstash-filters.mdx"
INGESTION_META_PATH = ROOT / "src/pages/log-management/ingestion-pipeline/_meta.json"

# Must match EXCLUDED_PLUGINS in sync-filter-options.py.
EXCLUDED_PLUGINS: set[str] = {
    "dns",
    "elastic_integration",
    "elasticsearch",
    "http",
    "jdbc_streaming",
    "memcached",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def slug_for(plugin: str) -> str:
    return plugin.replace("_", "-")


def check_plugin_page(path: Path, plugin: str) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing page: {path.relative_to(ROOT)}"]

    text = path.read_text(encoding="utf-8")
    required_markers = [
        "## Options",
        "## Example configuration",
        "## References",
    ]
    for marker in required_markers:
        if marker not in text:
            errors.append(f"{path.relative_to(ROOT)} missing section: {marker}")

    if f"`{plugin}`" not in text and plugin not in text:
        errors.append(f"{path.relative_to(ROOT)} does not reference plugin token `{plugin}`")

    if "## Example configuration" in text:
        parts = text.split("## Example configuration", 1)
        tail = parts[1]
        until_next = tail.split("\n## ", 1)[0]
        if "filter {" not in until_next:
            errors.append(f"{path.relative_to(ROOT)} example section missing `filter {{` block")

    return errors


def main() -> int:
    inventory = load_json(INVENTORY_PATH)
    authored = load_json(AUTHORED_PATH) if AUTHORED_PATH.exists() else {"plugins": {}}
    authored_plugins: dict = authored.get("plugins", {}) or {}
    filter_meta = load_json(FILTER_META_PATH)
    ingestion_meta = load_json(INGESTION_META_PATH)

    errors: list[str] = []
    included_plugins = [item["plugin"] for item in inventory["plugins"] if item["plugin"] not in EXCLUDED_PLUGINS]
    excluded_plugins = [item["plugin"] for item in inventory["plugins"] if item["plugin"] in EXCLUDED_PLUGINS]
    plugin_slugs = [slug_for(plugin) for plugin in included_plugins]

    for plugin in included_plugins:
        slug = slug_for(plugin)
        page_path = FILTER_DIR / f"{slug}.mdx"
        errors.extend(check_plugin_page(page_path, plugin))
        if plugin not in authored_plugins:
            errors.append(f"authored content missing for plugin: {plugin}")

    for plugin in excluded_plugins:
        slug = slug_for(plugin)
        page_path = FILTER_DIR / f"{slug}.mdx"
        if page_path.exists():
            errors.append(f"excluded plugin page should not exist: {page_path.relative_to(ROOT)}")

    for slug in plugin_slugs:
        if slug not in filter_meta:
            errors.append(f"filter meta missing key: {slug}")

    for slug in filter_meta:
        page_path = FILTER_DIR / f"{slug}.mdx"
        if not page_path.exists():
            errors.append(f"filter meta references missing page: {slug}")

    reference_text = REFERENCE_PATH.read_text(encoding="utf-8")
    for plugin in included_plugins:
        if f"`{plugin}`" not in reference_text:
            errors.append(f"reference page missing plugin entry: {plugin}")

    if "logstash-filters" not in ingestion_meta:
        errors.append("ingestion _meta.json missing `logstash-filters` key")
    if "logstash-filters-reference" not in ingestion_meta:
        errors.append("ingestion _meta.json missing `logstash-filters-reference` key")
    if "<FolderBrowser />" not in HUB_PATH.read_text(encoding="utf-8"):
        errors.append("hub page missing FolderBrowser component")

    # License-safety check: no third-party documentation hosts should be linked
    # from any generated filter page (plugin source repos on GitHub are allowed).
    url_re = re.compile(r"https?://([a-zA-Z0-9.-]+)")
    allowed_hosts = {"logit.io", "www.logit.io", "docs.logit.io", "github.com"}
    for slug in plugin_slugs:
        page_path = FILTER_DIR / f"{slug}.mdx"
        text = page_path.read_text(encoding="utf-8")
        for host in url_re.findall(text):
            host_lower = host.lower()
            if host_lower in allowed_hosts or host_lower.endswith(".logit.io"):
                continue
            errors.append(f"{page_path.relative_to(ROOT)} contains disallowed external host: {host_lower}")

    fence_re = re.compile(r"```")
    for slug in plugin_slugs:
        page_path = FILTER_DIR / f"{slug}.mdx"
        text = page_path.read_text(encoding="utf-8")
        fences = len(fence_re.findall(text))
        if fences % 2 != 0:
            errors.append(f"unbalanced code fences: {page_path.relative_to(ROOT)}")

    if errors:
        print("QA FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("QA PASSED")
    print(f"- plugin pages checked: {len(plugin_slugs)}")
    print(f"- filter meta entries: {len(filter_meta)}")
    print(f"- reference page: {REFERENCE_PATH.relative_to(ROOT)}")
    print(f"- hub page: {HUB_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
