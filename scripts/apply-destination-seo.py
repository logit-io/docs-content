#!/usr/bin/env python3
"""One-off / repeatable: unique metaTitle, description, and intro lead for each alert destination."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "src/pages/log-management/alerting/destinations"

# Shared short closers (rotate to reduce duplicate body copy across pages).
NAV = [
    "**[Options](#options)** covers each YAML field—required first—with snippets under some keys. **[Full working example](#full-working-example)** at the bottom is a complete rule for the Logit.io alert editor.",
    "Field reference lives under **[Options](#options)**; **[Full working example](#full-working-example)** at the end shows full YAML (`name`, `type`, `index`, `filter`, and this destination).",
    "Use **[Options](#options)** for key-by-key reference, then **[Full working example](#full-working-example)** for copy-paste YAML you can tailor to your stack.",
    "Skim **[Options](#options)** for required vs optional keys, then open **[Full working example](#full-working-example)** for runnable YAML including `index` and `filter`.",
    "Details for each key are in **[Options](#options)**; **[Full working example](#full-working-example)** ties the destination into a full ElastAlert 2 rule.",
    "Start with **[Options](#options)** when wiring credentials and endpoints—**[Full working example](#full-working-example)** shows how they fit in a complete rule.",
]

# filename -> (metaTitle, description, intro_lead_paragraph only — nav appended)
# intro_lead must end with sentence punctuation; we add `alert` token + nav in script for standard pages.
SEO: dict[str, tuple[str, str, str]] = {
    "alerta.mdx": (
        "Alerta API alerts from log rules — Logit.io",
        "Send OpenSearch log matches to Alerta’s HTTP API with ElastAlert 2 on Logit.io: `alerta`, attributes, severity, and a full YAML example.",
        "Route firing rules into **Alerta** so operators see a single console for correlated incidents. Add `alerta` under `alert:` and point `alerta_api_url` at your Alerta deployment.",
    ),
    "alertmanager.mdx": (
        "Prometheus Alertmanager from ElastAlert 2 — Logit.io",
        "Forward Log Management alerts to Prometheus **Alertmanager** via ElastAlert 2: labels, annotations, `alertmanager` YAML, and a working rule for Logit.io.",
        "Push log-derived incidents into **Alertmanager** for silencing, routing, and inhibition alongside metrics alerts. Use `alertmanager` in the `alert` list and map labels and annotations to your receivers.",
    ),
    "amazon-ses.mdx": (
        "AWS SES email alerts — Log Management | Logit.io",
        "Send alert emails through **Amazon SES** from ElastAlert 2 on Logit.io: `ses`, regions, credentials, CC/BCC, and a complete YAML rule.",
        "Deliver alert mail through **Amazon SES** instead of raw SMTP—ideal when you already standardise on AWS for outbound email. Set `alert: ses` and supply `ses_email`, `ses_from_addr`, and AWS auth as needed.",
    ),
    "amazon-sns.mdx": (
        "Amazon SNS notifications — Logit.io alerting",
        "Publish ElastAlert 2 matches to an **Amazon SNS** topic from Logit.io: `sns`, topic ARN, AWS keys, and an example rule YAML.",
        "Fan out log alerts to email, SMS, Lambda, or queues by publishing to **SNS**. Add `sns` to `alert:` and set `sns_topic_arn` plus optional AWS credential keys.",
    ),
    "amazon-sqs.mdx": (
        "Amazon SQS alert messages — Logit.io",
        "Enqueue log alerts on **Amazon SQS** with ElastAlert 2 on Logit.io: `sqs`, queue URL, boto credentials, and sample YAML.",
        "Hand matches to workers or decoupled pipelines by writing JSON messages to **SQS**. Configure `sqs` with your queue URL and AWS access settings.",
    ),
    "chatwork.mdx": (
        "Chatwork room notifications — Logit.io",
        "Post ElastAlert 2 notifications to **Chatwork** from Logit.io managed log alerting: `chatwork`, API token, room ID, and example YAML.",
        "Notify a **Chatwork** room when a rule fires so on-call teams see context in chat. Add `chatwork` under `alert:` with your API credentials and target room.",
    ),
    "datadog.mdx": (
        "Datadog Events from logs — Logit.io",
        "Create **Datadog** events from OpenSearch matches via ElastAlert 2 on Logit.io: `datadog`, API/app keys, tags, and YAML.",
        "Surface log-based incidents on your **Datadog** event stream for correlation with APM and infrastructure metrics. Use `datadog` in `alert:` with your API and application keys.",
    ),
    "debug.mdx": (
        "Debug alerter — ElastAlert logging — Logit.io",
        "Trace ElastAlert 2 output with the **debug** destination on Logit.io: logger name, log level, and a minimal YAML rule.",
        "Inspect match payloads and rule behaviour without leaving the platform. Add `debug` to `alert:` and watch the `elastalert` logger when troubleshooting rules.",
    ),
    "dingtalk.mdx": (
        "DingTalk bot alerts — Logit.io",
        "Send **DingTalk** group or chatbot messages from ElastAlert 2 on Logit.io: `dingtalk`, webhooks, keywords, and YAML options.",
        "Reach teams on **DingTalk** when log patterns breach thresholds. Configure `dingtalk` with webhook URLs, signatures, or phone lists depending on your integration style.",
    ),
    "discord.mdx": (
        "Discord webhook alerts — Logit.io",
        "Post log alerts to **Discord** channels via webhook with ElastAlert 2 on Logit.io: `discord`, embeds, and a working YAML example.",
        "Mirror incidents into a **Discord** server for developers and SREs. Add `discord` under `alert:` and supply the channel webhook URL and optional embed styling.",
    ),
    "email.mdx": (
        "SMTP email alerts — Log Management | Logit.io",
        "Send **email** notifications from ElastAlert 2 on Logit.io: SMTP, TLS, HTML bodies, attachments, and a full rule YAML.",
        "The classic **email** destination delivers subjects and bodies built from your rule’s formatting settings over SMTP. Use `email` in `alert:` with `email` recipients and mail server options.",
    ),
    "exotel.mdx": (
        "Exotel voice/SMS alerts — Logit.io",
        "Trigger **Exotel** calls or SMS when logs match using ElastAlert 2 on Logit.io: `exotel`, SID, tokens, and sample YAML.",
        "Escalate with a phone call or SMS through **Exotel**’s telephony APIs. Add `exotel` to `alert:` with your account SID, token, and destination numbers.",
    ),
    "flashduty.mdx": (
        "Flashduty incident alerts — Logit.io",
        "Open **Flashduty** incidents from log rules with ElastAlert 2 on Logit.io: `flashduty`, API keys, routing, and YAML reference.",
        "Feed **Flashduty** with structured incidents derived from OpenSearch queries. Configure `flashduty` with API credentials and routing fields your organisation requires.",
    ),
    "gelf.mdx": (
        "Graylog GELF log alerts — Logit.io",
        "Ship alert context to **Graylog** over GELF (UDP/TCP) from ElastAlert 2 on Logit.io: `gelf`, host, port, TLS, and YAML.",
        "Send a GELF message per match so **Graylog** can index alert metadata alongside application logs. Use `gelf` with your Graylog input host, port, and optional TLS.",
    ),
    "gitter.mdx": (
        "Gitter room messages — Logit.io",
        "Post to **Gitter** rooms from ElastAlert 2 on Logit.io: `gitter`, auth token, room, and example YAML (legacy integration).",
        "Notify a **Gitter** room when a rule fires—useful for communities still on Gitter-style workflows. Add `gitter` under `alert:` with token and room identifiers.",
    ),
    "googlechat.mdx": (
        "Google Chat webhook alerts — Logit.io",
        "Notify **Google Chat** spaces from ElastAlert 2 on Logit.io: `googlechat`, incoming webhooks, thread keys, and full YAML.",
        # Custom combined intro handled below — placeholder unused if SPECIAL
        "",
    ),
    "grafana-irm.mdx": (
        "Grafana OnCall & IRM — ElastAlert webhook — Logit.io",
        "Connect Logit.io **ElastAlert 2** rules to **Grafana IRM / OnCall** using the HTTP integration: `post`, payload mapping, and example rule YAML.",
        "",
    ),
    "hivealerter.mdx": (
        "TheHive case alerts — Logit.io",
        "Create **TheHive** alerts or cases from log matches via ElastAlert 2 on Logit.io: `hivealerter`, API URL, templates, and YAML.",
        "Turn suspicious log patterns into **TheHive** observables and cases for your SOC. Configure `hivealerter` with API keys, instance URL, and case templates.",
    ),
    "indexer.mdx": (
        "Indexer alerter — write matches to OpenSearch — Logit.io",
        "Write ElastAlert 2 matches back into an **OpenSearch** index on Logit.io using `indexer`: connection, index name, and YAML.",
        "Archive or enrich data by indexing each match into a dedicated **OpenSearch** index for dashboards or downstream jobs. Use `indexer` with host, index, and type settings.",
    ),
    "iris.mdx": (
        "DFIR-IRIS incident alerts — Logit.io",
        "Raise **DFIR-IRIS** incidents from log rules with ElastAlert 2 on Logit.io: `iris`, API URL, SSL, custom fields, and YAML.",
        "Push structured incidents into **IRIS** for digital forensics and IR workflows. Add `iris` under `alert:` with server URL, API key, and case metadata fields.",
    ),
    "jira.mdx": (
        "Jira issues from log alerts — Logit.io",
        "Open **Jira** tickets automatically from ElastAlert 2 on Logit.io: `jira`, projects, issue types, custom fields, and YAML.",
        "Create or update **Jira** work items when log rules fire so engineering tracks remediation in your existing backlog. Use `jira` with project, issue type, and authentication options.",
    ),
    "lark.mdx": (
        "Lark / Feishu bot alerts — Logit.io",
        "Send **Lark** (Feishu) bot messages from ElastAlert 2 on Logit.io: `lark`, webhook secrets, signing, and example YAML.",
        "Notify collaboration hubs on **Lark** with signed webhook requests. Configure `lark` with your bot webhook and verification settings.",
    ),
    "line.mdx": (
        "LINE Notify alerts — Logit.io",
        "Deliver **LINE** push notifications from ElastAlert 2 on Logit.io: `line`, channel access token, user ID, and YAML.",
        "Reach people on **LINE** when critical log patterns match. Add `line` to `alert:` with a channel access token and target user or group identifiers.",
    ),
    "matrixhookshot.mdx": (
        "Matrix Hookshot webhooks — Logit.io",
        "Post to **Matrix** rooms via Hookshot webhooks from ElastAlert 2 on Logit.io: `matrixhookshot`, URLs, and YAML.",
        "Mirror alerts into a **Matrix** room using Hookshot-compatible webhooks. Use `matrixhookshot` with the room webhook URL and formatting options.",
    ),
    "mattermost.mdx": (
        "Mattermost incoming webhooks — Logit.io",
        "Send **Mattermost** messages from ElastAlert 2 on Logit.io: `mattermost`, channels, icons, attachments, and full YAML.",
        "Surface incidents in **Mattermost** for self-hosted teams. Add `mattermost` under `alert:` with webhook URL, channel override, and rich attachment fields as needed.",
    ),
    "ms-power-automate.mdx": (
        "Power Automate HTTP triggers — Logit.io",
        "Trigger **Microsoft Power Automate** flows from log alerts via ElastAlert 2 on Logit.io: `ms_power_automate`, HTTP POST, and YAML.",
        "Kick off low-code automation when OpenSearch rules fire by POSTing to a **Power Automate** HTTP trigger. Configure `ms_power_automate` with the generated request URL and payload options.",
    ),
    "ms-teams.mdx": (
        "Microsoft Teams connector alerts — Logit.io",
        "Post to **Microsoft Teams** channels from ElastAlert 2 on Logit.io: `ms_teams`, webhook URLs, themes, proxies, and YAML.",
        "Deliver card-style messages to **Teams** using an incoming webhook connector. Use `ms_teams` in `alert:` with the webhook URL and optional theme or proxy settings.",
    ),
    "opsgenie.mdx": (
        "Opsgenie alerts from logs — Logit.io",
        "Create **Opsgenie** alerts from ElastAlert 2 on Logit.io: `opsgenie`, API keys, teams, priorities, responders, and YAML.",
        "Page the right responders through **Opsgenie** when log-derived rules breach. Add `opsgenie` with your API key, message templates, and routing fields.",
    ),
    "pagerduty.mdx": (
        "PagerDuty incidents — Log Management | Logit.io",
        "Open **PagerDuty** incidents from OpenSearch rules via ElastAlert 2 on Logit.io: `pagerduty`, routing keys, custom details, dedup, and YAML.",
        "Turn matches into **PagerDuty** incidents with explicit severity, routing keys, and custom detail payloads. Use `pagerduty` under `alert:` with your integration credentials.",
    ),
    "pagertree.mdx": (
        "PagerTree on-call routing — Logit.io",
        "Notify **PagerTree** schedules from ElastAlert 2 on Logit.io: `pagertree`, integration URL, and minimal YAML.",
        "Hand off log alerts to **PagerTree**’s on-call rotations via a dedicated integration URL. Add `pagertree` to `alert:` with the endpoint Log Management should POST to.",
    ),
    "post.mdx": (
        "Custom HTTP POST webhooks — ElastAlert post — Logit.io",
        "POST JSON alert payloads to any HTTPS URL with ElastAlert 2 **`post`** on Logit.io: field mapping, headers, static payload, and full YAML.",
        "",
    ),
    "post2.mdx": (
        "HTTP POST with Jinja — post2 webhooks — Logit.io",
        "Build JSON bodies with **Jinja2** using ElastAlert 2 **`post2`** on Logit.io: templated payload and headers, quoting tips, and YAML.",
        "",
    ),
    "rocketchat.mdx": (
        "Rocket.Chat incoming webhooks — Logit.io",
        "Send **Rocket.Chat** messages from ElastAlert 2 on Logit.io: `rocketchat`, channels, attachments, auth, and YAML reference.",
        "Notify **Rocket.Chat** channels or DMs when rules fire. Configure `rocketchat` with webhook URL, channel overrides, and attachment payloads.",
    ),
    "servicenow.mdx": (
        "ServiceNow incidents from logs — Logit.io",
        "Create **ServiceNow** incidents via ElastAlert 2 on Logit.io: `servicenow`, REST credentials, tables, fields, and YAML.",
        "Raise **ServiceNow** tickets with CMDB-aware fields when log thresholds trip. Use `servicenow` with instance URL, credentials, and table mappings.",
    ),
    "slack.mdx": (
        "Slack notifications — Log Management | Logit.io",
        "Send **Slack** messages from ElastAlert 2 on Logit.io: `slack`, webhooks, `slack_channel_override`, formatting, icons, and full YAML.",
        "Deliver rich **Slack** notifications with channel overrides, emoji, and attachment blocks. Add `slack` under `alert:` with webhook or API-style settings per your workspace policy.",
    ),
    "smseagle.mdx": (
        "SMSEagle hardware SMS gateway — Logit.io",
        "Send SMS through an **SMSEagle** appliance from ElastAlert 2 on Logit.io: `smseagle`, host, users, modem groups, and YAML.",
        "Use an on-prem **SMSEagle** device as your SMS path for critical alerts. Configure `smseagle` with device URL, credentials, and recipient groups.",
    ),
    "stomp.mdx": (
        "STOMP message broker alerts — Logit.io",
        "Publish matches to a **STOMP** broker from ElastAlert 2 on Logit.io: `stomp`, host, login, destination, SSL, and YAML.",
        "Integrate with brokers that speak **STOMP** (for example ActiveMQ-style setups). Add `stomp` with connection parameters and the queue or topic destination.",
    ),
    "telegram.mdx": (
        "Telegram bot alerts — Logit.io",
        "Message **Telegram** chats via bot API from ElastAlert 2 on Logit.io: `telegram`, token, proxies, parse modes, and YAML.",
        "Ping engineers on **Telegram** using a bot token and chat ID. Use `telegram` under `alert:` with optional proxy and formatting options.",
    ),
    "tencent-sms.mdx": (
        "Tencent Cloud SMS alerts — Logit.io",
        "Send SMS through **Tencent Cloud** from ElastAlert 2 on Logit.io: `tencent_sms`, SDK app ID, signatures, templates, and YAML.",
        "Deliver SMS in Tencent’s ecosystem using **Tencent Cloud SMS** APIs. Configure `tencent_sms` with application ID, template parameters, and phone number lists.",
    ),
    "twilio.mdx": (
        "Twilio SMS & voice alerts — Logit.io",
        "Trigger **Twilio** SMS or calls from ElastAlert 2 on Logit.io: `twilio`, Account SID, auth, From/To numbers, and YAML.",
        "Reach on-call staff via **Twilio**’s programmable messaging or voice APIs. Add `twilio` with account credentials and verified sender identifiers.",
    ),
    "victorops.mdx": (
        "Splunk On-Call (VictorOps) routing — Logit.io",
        "Route log alerts to **Splunk On-Call** with ElastAlert 2 on Logit.io: `victorops`, REST URLs, routing keys, entity fields, and YAML.",
        "Send OpenSearch-derived incidents to **VictorOps / Splunk On-Call** using the REST integration endpoint. Use `victorops` with your API URL and routing metadata.",
    ),
    "webex-webhook.mdx": (
        "Webex incoming webhook alerts — Logit.io",
        "Post to **Webex** spaces from ElastAlert 2 on Logit.io: `webex_webhook`, room IDs, bot tokens, and YAML.",
        "Notify a **Webex** space when rules fire using an incoming webhook–style flow. Configure `webex_webhook` with room ID and bot authentication.",
    ),
    "workwechat.mdx": (
        "WeCom enterprise messages — Logit.io",
        "Send **WeCom (Work WeChat)** app messages from ElastAlert 2 on Logit.io: `workwechat`, corp ID, agent ID, secrets, and YAML.",
        "Reach employees on **WeCom** through your enterprise application. Add `workwechat` with corporate credentials, agent ID, and user or party targets.",
    ),
    "yzj.mdx": (
        "YZJ enterprise notifications — Logit.io",
        "Integrate **YZJ** messaging from ElastAlert 2 on Logit.io: `yzj`, app credentials, user lists, and YAML options.",
        "Deliver alerts through your **YZJ** deployment using the documented YAML keys. Add `yzj` under `alert:` and supply the app and user parameters your tenant requires.",
    ),
    "zabbix.mdx": (
        "Zabbix trapper alerts — Logit.io",
        "Send **Zabbix** trapper items from ElastAlert 2 on Logit.io: `zabbix`, server host, keys, fields, and YAML.",
        "Feed **Zabbix** with trapper-style data so log-derived events appear in monitoring. Configure `zabbix` with server, port, host key, and field mappings.",
    ),
}

FRONTMATTER_RE = re.compile(
    r"^(---\n)(.*?)(\n---\n)",
    re.DOTALL | re.MULTILINE,
)

INTRO_RE = re.compile(
    r"(^(# [^\n]+\n\n))(.*?)(\n## Options\n)",
    re.DOTALL | re.MULTILINE,
)


def plain_meta_description(s: str) -> str:
    """Strip markdown from meta descriptions for clean SERP snippets."""
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def patch_meta(text: str, meta_title: str, description: str) -> str:
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
        if not seen_mt:
            raise ValueError("metaTitle missing")
        if not seen_desc:
            raise ValueError("description missing")
        return m.group(1) + "\n".join(out) + m.group(3)

    return FRONTMATTER_RE.sub(repl, text, count=1)


def _already_has_alert_clause(lead: str) -> bool:
    return bool(
        re.search(
            r"(under `alert:`|in the `alert` list|`alert`\s*:\s*\w|Set `alert:)",
            lead,
        )
    )


def standard_intro(lead: str, token: str, nav_i: int) -> str:
    nav = NAV[nav_i % len(NAV)]
    lead = lead.strip()
    if not _already_has_alert_clause(lead):
        lead = f"{lead.rstrip('.')}. Add `{token}` under `alert:` on your rule (you can combine destinations)."
    return f"{lead}\n\n{nav}"


SPECIAL_INTROS: dict[str, str] = {
    "googlechat.mdx": """Send notifications to a **Google Chat** space by adding `googlechat` to the `alert` list and configuring a **webhook URL** from that space’s app configuration. The alert **body** comes from your rule’s normal text settings — see [Subject & body](/log-management/alerting/alert-subject-and-body).

**[Options](#options)** lists every `googlechat_*` key; **[Full working example](#full-working-example)** at the bottom is a complete YAML rule for the Logit.io editor.""",
    "grafana-irm.mdx": """[Grafana IRM](https://grafana.com/docs/grafana-cloud/alerting-and-irm/) (including **Grafana OnCall**) can receive alerts through an **HTTP / ElastAlert**-style inbound integration: your rule POSTs JSON to a webhook URL that OnCall shows in the integration settings.

On Logit.io you normally use the **`post`** destination and set `http_post_url` to that **integration URL** (copy it from Grafana OnCall and replace the placeholder in the example below). **[Options](#options)** summarises the `post` keys that matter for OnCall; **[Example rule](#example-rule)** at the bottom is full YAML—swap in your real integration URL.""",
    "post.mdx": """This destination uses ElastAlert 2’s **`post`** alerter to send alert matches as **JSON POST** requests to any HTTPS URL—custom webhooks, Zapier, internal APIs, Squadcast, and similar. In your rule YAML, set `alert: post`, then configure `http_post_url` and any optional payload and header mappings.

**[Options](#options)** documents every key; **[Full working example](#full-working-example)** at the bottom is end-to-end YAML for the Logit.io alert editor.""",
    "post2.mdx": """Same idea as the [simple HTTP POST webhook](/log-management/alerting/destinations/post), but **`post2`** lets you use **Jinja2** in `http_post2_payload` and `http_post2_headers` so values can reference fields from the match (including nested keys via `_data` and `jinja_root_name`).

<Callout type="info">
  In YAML key/value form, prefer single quotes around values that contain Jinja so parsing stays predictable.
</Callout>

**[Options](#options)** walks through each `post2` key; **[Full working example](#full-working-example)** at the bottom is a complete rule that shows Jinja in the payload and headers.""",
}

ALERT_TOKENS: dict[str, str] = {
    "amazon-ses.mdx": "ses",
    "amazon-sns.mdx": "sns",
    "amazon-sqs.mdx": "sqs",
    "webex-webhook.mdx": "webex_webhook",
    "ms-teams.mdx": "ms_teams",
    "ms-power-automate.mdx": "ms_power_automate",
    "tencent-sms.mdx": "tencent_sms",
}


def alert_token_for(filename: str) -> str:
    if filename in ALERT_TOKENS:
        return ALERT_TOKENS[filename]
    stem = filename.removesuffix(".mdx")
    return stem.replace("-", "_")


def main() -> None:
    for i, (fname, (mt, desc, lead)) in enumerate(sorted(SEO.items())):
        path = DEST / fname
        text = path.read_text(encoding="utf-8")
        text = patch_meta(text, mt, desc)
        if fname in SPECIAL_INTROS:
            new_intro_body = SPECIAL_INTROS[fname]
        else:
            if not lead.strip():
                raise ValueError(f"empty lead for {fname}")
            tok = alert_token_for(fname)
            new_intro_body = standard_intro(lead.strip(), tok, i)
        m = INTRO_RE.search(text)
        if not m:
            raise RuntimeError(f"intro pattern failed: {fname}")
        remainder = text[m.end() :]
        text = (
            text[: m.start()]
            + m.group(1)
            + new_intro_body.rstrip()
            + "\n\n## Options\n"
            + remainder
        )
        path.write_text(text, encoding="utf-8")
        print("patched", fname)


if __name__ == "__main__":
    main()
