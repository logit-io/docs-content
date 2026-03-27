#!/usr/bin/env python3
"""Unique metaTitle/description, SEO intro, and Options layout for ElastAlert rule type pages."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "src/pages/log-management/alerting/rule-types"

OPTIONS_BLURB = (
    "The bullets below are **only** the fields that belong to **`type: {t}`**. "
    "The same rule YAML still defines your OpenSearch **`filter`** and **`index`**, your **`alert`** destinations, "
    "and cross-type settings such as **`buffer_time`**, **`run_every`**, **`realert`**, and Discover-link fields. "
    "Those shared options apply to every rule—for the exhaustive YAML list see "
    "[Full Reference](/log-management/alerting/alert-reference); for how to build rules on Logit.io see "
    "[Create a rule](/log-management/alerting/creating-alerts), "
    "[Subject & body](/log-management/alerting/alert-subject-and-body), "
    "[Context & links](/log-management/alerting/alert-context-and-links), and "
    "[Destinations](/log-management/alerting/destinations)."
)

NAV = [
    "**[Options](#options)** lists type-specific keys (required and optional). **[Full working example](#full-working-example)** is a runnable rule for the Logit.io editor.",
    "Use **[Options](#options)** for field-by-key reference, then **[Full working example](#full-working-example)** for copy-paste YAML including `filter` and `alert`.",
    "Skim **[Options](#options)** for required vs optional fields, then open **[Full working example](#full-working-example)** for a complete `type: {t}` example.",
    "**[Options](#options)** covers what this rule type adds beyond shared rule fields; **[Full working example](#full-working-example)** shows it end-to-end.",
    "Details for each key are in **[Options](#options)**; **[Full working example](#full-working-example)** ties `type: {t}` into a full ElastAlert 2 rule.",
    "Start with **[Options](#options)** when tuning thresholds and windows—**[Full working example](#full-working-example)** shows a realistic index and query.",
]

# filename -> (metaTitle, description with optional ** for stripping, lead paragraphs before existing body)
RULE_SEO: dict[str, tuple[str, str, str]] = {
    "any.mdx": (
        "Any rule type — alert on every match — Logit.io",
        "Use ElastAlert 2 **type: any** on Logit.io to notify on every document that matches your filter, with realert, query_key, and YAML examples.",
        "The **any** rule fires once per matching document—ideal when each hit should surface immediately, or when you throttle with `realert` and `query_key`.",
    ),
    "blacklist.mdx": (
        "Blacklist rule — deny-list field values — Logit.io",
        "Alert when a field equals a forbidden value using ElastAlert 2 **type: blacklist** on Logit.io: compare_key, list values, and YAML.",
        "The **blacklist** rule matches when `compare_key` appears in your deny list—common for status codes, IPs, or policy violations.",
    ),
    "whitelist.mdx": (
        "Whitelist rule — allow-list field values — Logit.io",
        "Alert when a value is **not** in an allow list using ElastAlert 2 **type: whitelist** on Logit.io, with compare_key and full YAML.",
        "The **whitelist** rule is the inverse of blacklist: it fires when `compare_key` is **outside** your approved set of values.",
    ),
    "change.mdx": (
        "Change rule — field changes per entity — Logit.io",
        "Detect when a field changes for the same user or host with ElastAlert 2 **type: change** on Logit.io: compare_key, query_key, timeframe.",
        "The **change** rule compares the current value of `compare_key` to the last seen value for the same `query_key`—useful for geo, role, or config drift.",
    ),
    "frequency.mdx": (
        "Frequency rule — N events in a window — Logit.io",
        "Alert when at least **num_events** occur in **timeframe** using ElastAlert 2 **type: frequency** on Logit.io, with count queries and examples.",
        "The **frequency** rule counts documents in a sliding window and fires when the total reaches `num_events`—optionally per `query_key` bucket.",
    ),
    "spike.mdx": (
        "Spike rule — volume vs previous window — Logit.io",
        "Compare current vs reference traffic with ElastAlert 2 **type: spike** on Logit.io: spike_height, spike_type, thresholds, and YAML.",
        "The **spike** rule compares two equal **timeframe** windows so you catch sudden surges or drops versus the prior period.",
    ),
    "flatline.mdx": (
        "Flatline rule — too few events — Logit.io",
        "Detect silence or missing heartbeats with ElastAlert 2 **type: flatline** on Logit.io: threshold, timeframe, query_key, and YAML.",
        "The **flatline** rule fires when event counts in `timeframe` fall **below** `threshold`—ideal for pipelines and heartbeat logs.",
    ),
    "new-term.mdx": (
        "New term rule — never-seen field values — Logit.io",
        "Alert on first-time values in a field using ElastAlert 2 **type: new_term** on Logit.io: fields, terms window, and YAML.",
        "The **new_term** rule learns baseline values over a scan window, then alerts when a new value appears in `fields`—watch user agents, IDs, or hosts.",
    ),
    "cardinality.mdx": (
        "Cardinality rule — distinct value counts — Logit.io",
        "Alert on too many or too few unique values with ElastAlert 2 **type: cardinality** on Logit.io: cardinality_field, max/min, query_key.",
        "The **cardinality** rule tracks how many distinct values `cardinality_field` has in `timeframe`—strong signal for credential stuffing or enumeration.",
    ),
    "metric-aggregation.mdx": (
        "Metric aggregation rule — avg, max, sum thresholds — Logit.io",
        "Threshold metrics from OpenSearch aggregations with ElastAlert 2 **type: metric_aggregation** on Logit.io: metric_agg_key, thresholds, YAML.",
        "The **metric_aggregation** rule evaluates min, max, avg, sum, percentiles, and more over `metric_agg_key`, then compares to `max_threshold` / `min_threshold`.",
    ),
    "spike-aggregation.mdx": (
        "Spike aggregation rule — metric spikes — Logit.io",
        "Spike detection on aggregated metrics with ElastAlert 2 **type: spike_aggregation** on Logit.io: buffer_time, metric_agg_key, spike_height.",
        "**spike_aggregation** works like **spike** but on a **metric** (e.g. average latency) instead of raw document counts between windows.",
    ),
    "percentage-match.mdx": (
        "Percentage match rule — share of matching docs — Logit.io",
        "Alert when a subset exceeds a percentage of hits using ElastAlert 2 **type: percentage_match** on Logit.io: match_bucket_filter, SLO-style YAML.",
        "The **percentage_match** rule measures what fraction of documents in `filter` also match `match_bucket_filter`—classic error-rate and SLO patterns.",
    ),
}

FRONTMATTER_RE = re.compile(r"^(---\n)(.*?)(\n---\n)", re.DOTALL | re.MULTILINE)
BODY_AFTER_FM_RE = re.compile(r"^---\n.*?\n---\n\n", re.DOTALL | re.MULTILINE)


def plain_meta_description(s: str) -> str:
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def patch_frontmatter(text: str, meta_title: str, description: str) -> str:
    description = plain_meta_description(description)

    def repl(m: re.Match) -> str:
        block = m.group(2)
        lines = block.splitlines()
        out: list[str] = []
        seen_mt, seen_desc = False, False
        for line in lines:
            if line.startswith("metaTitle:"):
                out.append(f"metaTitle: {json.dumps(meta_title, ensure_ascii=False)}")
                seen_mt = True
            elif line.startswith("description:"):
                out.append(f"description: {json.dumps(description, ensure_ascii=False)}")
                seen_desc = True
            else:
                out.append(line)
        if not (seen_mt and seen_desc):
            raise ValueError("metaTitle or description missing")
        return m.group(1) + "\n".join(out) + m.group(3)

    return FRONTMATTER_RE.sub(repl, text, count=1)


def parse_frontmatter_title(text: str) -> str:
    m = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
    if not m:
        raise ValueError("title: missing in frontmatter")
    t = m.group(1).strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        t = t[1:-1]
    return t


def file_to_type_token(fname: str) -> str:
    return Path(fname).stem.replace("-", "_")


def normalize_body_h1(text: str, display_title: str) -> tuple[str, int]:
    """Use the same text as `title:` in frontmatter for the page H1 (standard docs pattern)."""
    m = BODY_AFTER_FM_RE.search(text)
    if not m:
        raise ValueError("expected --- frontmatter --- body")
    pre = text[: m.end()]
    body = text[m.end() :]
    body = re.sub(r"^# [^\n]+\n\n", "", body, count=1)
    h1 = f"# {display_title}\n\n"
    new_text = pre + h1 + body
    insert_at = len(pre) + len(h1)
    return new_text, insert_at


def remove_first_paragraph(middle: str) -> str:
    """Drop the opening explanatory paragraph; keep Callouts and ## sections."""
    s = middle.lstrip("\n")
    m = re.match(r"^[\s\S]+?(\n\n(?:<Callout|## ))", s)
    if m:
        return s[m.start(1) :]
    return s


def build_options_blurb(type_token: str) -> str:
    return OPTIONS_BLURB.format(t=type_token)


def transform_options_headings(chunk: str, type_token: str) -> str:
    blurb = build_options_blurb(type_token)
    m = re.search(r"(## Options\n+)([\s\S]*?)(\n+### Required\n)", chunk)
    if m:
        return chunk[: m.start(2)] + blurb + chunk[m.end(2) :]

    c = chunk
    if not re.search(r"^## Required\s*$", c, re.MULTILINE):
        raise ValueError("expected ## Options block or ## Required")
    c = re.sub(
        r"^## Required\s*$",
        f"## Options\n\n{blurb}\n\n### Required",
        c,
        count=1,
        flags=re.MULTILINE,
    )
    c = re.sub(r"^## Common options\s*$", "### Optional", c, count=1, flags=re.MULTILINE)
    c = re.sub(r"^## Optional\s*$", "### Optional", c, count=1, flags=re.MULTILINE)
    return c


def patch_file(path: Path, index: int) -> None:
    fname = path.name
    if fname not in RULE_SEO:
        return
    meta_title, desc_raw, lead = RULE_SEO[fname]
    text = path.read_text(encoding="utf-8")
    display_title = parse_frontmatter_title(text)
    type_token = file_to_type_token(fname)
    text = patch_frontmatter(text, meta_title, desc_raw)
    text, insert_at = normalize_body_h1(text, display_title)
    nav = NAV[index % len(NAV)].format(t=type_token)
    prefix = f"{lead}\n\n{nav}\n\n"

    idx_full = text.find("\n## Full working example\n")
    if idx_full == -1:
        raise RuntimeError(f"## Full working example not found: {fname}")

    head = text[:insert_at]
    middle = text[insert_at:idx_full]
    tail = text[idx_full:]

    if not middle.startswith(lead):
        middle = prefix + remove_first_paragraph(middle)

    middle = transform_options_headings(middle, type_token)
    path.write_text(head + middle + tail, encoding="utf-8")
    print("patched", fname)


def main() -> None:
    paths = sorted(RULE_DIR.glob("*.mdx"))
    idx = 0
    for path in paths:
        if path.name.startswith("_") or path.name not in RULE_SEO:
            continue
        patch_file(path, idx)
        idx += 1


if __name__ == "__main__":
    main()
