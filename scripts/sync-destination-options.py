#!/usr/bin/env python3
"""
Extract alerter options and example YAML/JSON from alert-reference.mdx and
rewrite destination pages. Examples are placed under the option they belong to.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF_PATH = ROOT / "src/pages/log-management/alerting/alert-reference.mdx"
DEST_DIR = ROOT / "src/pages/log-management/alerting/destinations"

SECTION_FILE = {
    "Alerta": "alerta.mdx",
    "Alertmanager": "alertmanager.mdx",
    "AWS SES (Amazon Simple Email Service)": "amazon-ses.mdx",
    "AWS SNS (Amazon Simple Notification Service)": "amazon-sns.mdx",
    "AWS SQS (Amazon Simple Queue Service)": "amazon-sqs.mdx",
    "Chatwork": "chatwork.mdx",
    "Datadog": "datadog.mdx",
    "Debug": "debug.mdx",
    "Dingtalk": "dingtalk.mdx",
    "Discord": "discord.mdx",
    "Email": "email.mdx",
    "Exotel": "exotel.mdx",
    "Gitter": "gitter.mdx",
    "GoogleChat": "googlechat.mdx",
    "Graylog GELF": "gelf.mdx",
    "HTTP POST": "post.mdx",
    "HTTP POST 2": "post2.mdx",
    "Indexer": "indexer.mdx",
    "IRIS": "iris.mdx",
    "Jira": "jira.mdx",
    "Lark": "lark.mdx",
    "LINE Messaging API": "line.mdx",
    "Matrix Hookshot": "matrixhookshot.mdx",
    "Mattermost": "mattermost.mdx",
    "Microsoft Teams": "ms-teams.mdx",
    "Microsoft Power Automate": "ms-power-automate.mdx",
    "OpsGenie": "opsgenie.mdx",
    "PagerDuty": "pagerduty.mdx",
    "PagerTree": "pagertree.mdx",
    "Rocket.Chat": "rocketchat.mdx",
    "ServiceNow": "servicenow.mdx",
    "Slack": "slack.mdx",
    "SMSEagle": "smseagle.mdx",
    "Splunk On-Call (Formerly VictorOps)": "victorops.mdx",
    "Stomp": "stomp.mdx",
    "Telegram": "telegram.mdx",
    "Tencent SMS": "tencent-sms.mdx",
    "TheHive": "hivealerter.mdx",
    "Twilio": "twilio.mdx",
    "Webex Webhook": "webex-webhook.mdx",
    "WorkWechat": "workwechat.mdx",
    "Zabbix": "zabbix.mdx",
    "YZJ": "yzj.mdx",
    "Flashduty": "flashduty.mdx",
}

OPTION_RE = re.compile(r"^`([^`]+)`:\s*(.*)$")
HEADING_RE = re.compile(r"^#### (.+)$")
FENCE_RE = re.compile(r"^```(\w+)?\s*$")
TOP_LEVEL_YAML_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*|@[A-Za-z0-9_]+):\s*")


@dataclass
class OptionRecord:
    key: str
    desc: str
    required: bool
    examples: list[tuple[str, str, str]] = field(default_factory=list)


def is_example_caption(s: str) -> bool:
    if not s or s.startswith("#"):
        return False
    low = s.lower().strip()
    if low.startswith("for example") and low != "for example":
        return False
    if re.match(r"^example:\s*\+", low) or re.match(r"^example:\s*\d", low):
        return False
    if re.match(r"^(incorrect|correct) usage", low):
        return True
    if low.endswith(" example") and len(s) < 100:
        if re.match(r"^(for|see|the) example$", low):
            return False
        return True
    if re.match(r"^example\b", low):
        return True
    return False


def split_sections(text: str) -> dict[str, list[str]]:
    lines = text.splitlines()
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def unindent_yaml_block(code: str) -> str:
    """Strip common leading whitespace so indented fenced YAML still yields top-level keys."""
    lines = code.splitlines()
    indents: list[int] = []
    for ln in lines:
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        indents.append(len(ln) - len(ln.lstrip()))
    if not indents or min(indents) == 0:
        return code
    m = min(indents)
    return "\n".join(ln[m:] if len(ln) >= m else ln for ln in lines)


def extract_top_level_yaml_keys(code: str) -> list[str]:
    code = unindent_yaml_block(code)
    keys: list[str] = []
    for line in code.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            continue
        m = TOP_LEVEL_YAML_KEY.match(line)
        if m:
            keys.append(m.group(1).lstrip("@"))
    return keys


def pick_attach_key(
    records: list[OptionRecord],
    last_flushed_key: str | None,
    code: str,
    lang: str,
) -> str | None:
    if not records:
        return None
    if lang == "json":
        return last_flushed_key or records[-1].key
    ykeys = extract_top_level_yaml_keys(code)
    cfg = [k for k in ykeys if k != "alert"]
    record_keys = {r.key for r in records}
    sorted_rks = sorted(record_keys, key=len, reverse=True)
    # Document order: first config key wins (so composite blocks attach to the first
    # illustrated option, not a later key that happens to match an option name exactly).
    for k in cfg:
        if k in record_keys:
            return k
        for rk in sorted_rks:
            if k.startswith(rk + "_"):
                return rk
    return last_flushed_key or records[-1].key


# Scalar content without embedded quotes — safe to fix common upstream typos.
_SIMPLE_SCALAR = r"[A-Za-z0-9._\-:/]+"


def sanitize_yaml_example(code: str) -> str:
    """Fix common copy-paste errors in example YAML (e.g. doubled ' or stray ' before closing \")."""
    out: list[str] = []
    for line in code.splitlines():
        # key: 'value''  →  key: 'value'   (only when value has no interior single quotes)
        m = re.match(
            rf"^(\s*[^:]+:\s*')({_SIMPLE_SCALAR})''(\s*(?:#.*)?)$",
            line,
        )
        if m:
            line = f"{m.group(1)}{m.group(2)}'{m.group(3)}"
        else:
            # key: "value'"  →  key: "value"
            m2 = re.match(
                rf'^(\s*[^:]+:\s*")({_SIMPLE_SCALAR})\'"(\s*(?:#.*)?)$',
                line,
            )
            if m2:
                line = f'{m2.group(1)}{m2.group(2)}"{m2.group(3)}'
        out.append(line)
    return "\n".join(out)


def read_fence_block(body_lines: list[str], caption_index: int) -> tuple[str, str, str, int] | None:
    """Return (caption, lang, code, index_after_closing_fence) or None."""
    if caption_index >= len(body_lines):
        return None
    caption = body_lines[caption_index].strip().rstrip(":").strip()
    j = caption_index + 1
    while j < len(body_lines) and not body_lines[j].strip().startswith("```"):
        j += 1
    if j >= len(body_lines):
        return None
    fence_line = body_lines[j].strip()
    fm = FENCE_RE.match(fence_line)
    lang = (fm.group(1) or "yaml").lower() if fm else "yaml"
    if lang not in ("yaml", "json", "text", "bash", "shell"):
        lang = "yaml"
    j += 1
    code_lines: list[str] = []
    while j < len(body_lines):
        fl = body_lines[j]
        if fl.strip().startswith("```"):
            break
        code_lines.append(fl)
        j += 1
    code = "\n".join(code_lines).rstrip()
    if not code.strip():
        return None
    if lang == "yaml":
        code = sanitize_yaml_example(code)
    return (caption, lang, code, j + 1)


def parse_section(body_lines: list[str]) -> list[OptionRecord]:
    records: list[OptionRecord] = []
    bucket_required = True
    current_key: str | None = None
    current_desc: list[str] = []
    in_code = False
    last_flushed_key: str | None = None
    possible_values = False
    title_counts: dict[str, int] = {}

    def merge_desc() -> str:
        d = " ".join(x.strip() for x in current_desc if x.strip()).strip()
        return re.sub(r"\s+", " ", d)

    def flush() -> None:
        nonlocal current_key, current_desc, last_flushed_key
        if not current_key:
            return
        desc = merge_desc()
        records.append(OptionRecord(current_key, desc, bucket_required))
        last_flushed_key = current_key
        current_key = None
        current_desc = []

    i = 0
    while i < len(body_lines):
        line = body_lines[i].rstrip("\n")
        if line.strip().startswith("```"):
            flush()
            in_code = not in_code
            i += 1
            continue
        if in_code:
            i += 1
            continue

        s = line.strip()
        low = s.lower()

        if s == "Optional:" or ("optional" in low and s.endswith(":") and "argument" in low):
            flush()
            bucket_required = False
            possible_values = False
            i += 1
            continue
        if s == "Required:":
            flush()
            bucket_required = True
            possible_values = False
            i += 1
            continue
        if low.startswith("possible values"):
            possible_values = True
            i += 1
            continue
        if low in ("or", "and", "then:") or low.startswith("additional explanation"):
            possible_values = False
            i += 1
            continue

        m = OPTION_RE.match(line)
        if m:
            flush()
            current_key = m.group(1).strip()
            current_desc = [m.group(2).strip()] if m.group(2).strip() else []
            possible_values = False
            i += 1
            continue

        if is_example_caption(s):
            flush()
            block = read_fence_block(body_lines, i)
            if block:
                cap, lang, code, next_i = block
                title_counts[cap] = title_counts.get(cap, 0) + 1
                n = title_counts[cap]
                if n > 1:
                    cap = f"{cap} ({n})"
                ak = pick_attach_key(records, last_flushed_key, code, lang)
                if ak:
                    for r in records:
                        if r.key == ak:
                            r.examples.append((cap, lang, code))
                            break
                i = next_i
                continue
            i += 1
            continue

        if current_key and s and not s.startswith("#"):
            if is_example_caption(s):
                flush()
                continue
            if possible_values or s.startswith("- "):
                current_desc.append(s)
            elif not any(
                x in low
                for x in (
                    "single address",
                    "multiple address",
                    "example when",
                    "for example, if you",
                    "complete yaml",
                    "a few words",
                )
            ):
                current_desc.append(s)
            possible_values = False

        i += 1

    flush()
    return records


def postprocess_section(heading: str, records: list[OptionRecord]) -> None:
    if heading == "Chatwork":
        move = {"chatwork_proxy", "chatwork_proxy_login", "chatwork_proxy_pass"}
        for r in records:
            if r.key in move:
                r.required = False

    if heading == "Jira":
        file_fields = {"user", "password", "apikey"}
        records[:] = [r for r in records if r.key not in file_fields]
        for r in records:
            if r.key == "jira_account_file":
                d = r.desc.split("When using user/password")[0].strip()
                cred = (
                    "For Jira Cloud or username/password auth the file normally contains `user` and `password` "
                    "(use the Jira Cloud API token as `password`). For self-hosted Jira with a PAT, use `apikey` only."
                )
                r.desc = f"{d} {cred}".strip()
            if r.key == "jira_parent":
                r.desc = r.desc.split(" Then:")[0].strip()
            if r.key == "jira_bump_after_inactivity":
                r.desc = r.desc.split("> **Note:**")[0].strip()
                r.desc = r.desc.split("Arbitrary Jira fields:")[0].strip()


def format_option_bullet(rec: OptionRecord) -> list[str]:
    line = f"- `{rec.key}` — {rec.desc}" if rec.desc else f"- `{rec.key}`"
    out = [line, ""]
    for caption, lang, code in rec.examples:
        out.append(f"  **{caption}**")
        out.append("")
        out.append(f"  ```{lang} copy")
        for cl in code.splitlines():
            out.append(f"  {cl}")
        out.append("  ```")
        out.append("")
    if out[-1] == "":
        out.pop()
    return out


def format_options_md(heading: str, records: list[OptionRecord]) -> str:
    parts: list[str] = ["## Options", ""]
    parts.append(
        "Keys below match the ElastAlert 2 alerter. Shared rule fields such as `alert_subject` apply as described in [Subject & body](/log-management/alerting/alert-subject-and-body). "
        "**Example fragments** from the ElastAlert 2 reference appear indented under the option they illustrate (add your own `name`, `type`, `index`, and `filter` to make a full rule)."
    )
    parts.append("")

    if heading == "Debug" and not records:
        parts.append(
            "- No destination-specific YAML keys — add `debug` under `alert` only. Output is written to the Python logger named `elastalert` at INFO level."
        )
        parts.append("")
        return "\n".join(parts)

    required = [r for r in records if r.required]
    optional = [r for r in records if not r.required]

    parts.append("### Required")
    parts.append("")
    if required:
        for r in required:
            parts.extend(format_option_bullet(r))
            parts.append("")
    else:
        parts.append(
            "- *(See the [Full Reference](/log-management/alerting/alert-reference); required keys may be contextual.)*"
        )
        parts.append("")

    if optional:
        parts.append("### Optional")
        parts.append("")
        for r in optional:
            parts.extend(format_option_bullet(r))
            parts.append("")

    if heading == "Jira":
        parts.append(
            "You can also set arbitrary Jira fields using rule keys `jira_<field_name>` (snake_case), or map a match field into a custom field with `#fieldname` syntax (see the [Full Reference](/log-management/alerting/alert-reference))."
        )
        parts.append("")

    while parts and parts[-1] == "":
        parts.pop()
    parts.append("")
    return "\n".join(parts)


EXAMPLE_SNIPPETS_RE = re.compile(
    r"\n## Example snippets\n.*?(?=\n## Full working example\n|\n## Example rule\n|\Z)",
    re.DOTALL,
)


def patch_destination(filename: str, options_md: str) -> bool:
    path = DEST_DIR / filename
    if not path.exists():
        print(f"skip missing file: {filename}")
        return False
    text = path.read_text(encoding="utf-8")
    anchor_match = re.search(r"\n## (Full working example|Example rule)\n", text)
    if not anchor_match:
        print(f"skip unexpected structure: {filename}")
        return False

    block = options_md.rstrip() + "\n"
    patterns = [
        r"## Options\n.*?(?=\n## Full working example\n|\n## Example rule\n|\n## Example snippets\n)",
        r"(?:## Required configuration|## Required settings)(?:\n.*?)+?(?=\n## Full working example\n|\n## Example rule\n|\n## Example snippets\n)",
    ]
    new_text = text
    replaced = False
    for pat in patterns:
        new_text, n = re.subn(pat, block, new_text, count=1, flags=re.DOTALL)
        if n == 1:
            replaced = True
            break
    if not replaced:
        print(f"replace failed (options): {filename}")
        return False

    new_text, _ = EXAMPLE_SNIPPETS_RE.subn("", new_text, count=1)
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    ref = REF_PATH.read_text(encoding="utf-8")
    sections = split_sections(ref)
    for heading, filename in SECTION_FILE.items():
        body = sections.get(heading)
        if not body:
            print(f"no section: {heading}")
            continue
        records = parse_section(body)
        postprocess_section(heading, records)
        md = format_options_md(heading, records)
        ex_count = sum(len(r.examples) for r in records)
        if patch_destination(filename, md):
            print(f"updated {filename} ({len(records)} options, {ex_count} example blocks under keys)")


if __name__ == "__main__":
    main()
