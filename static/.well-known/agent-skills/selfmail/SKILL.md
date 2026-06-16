---
name: selfmail
description: Email yourself — or a configured address — from the shell or an AI agent, over Resend. Use when the user wants to send themselves an email, get notified by email from a script, cron job, CI, or agent, deliver command output or a file to their own inbox, or asks to "email me when this is done". Wraps the one-command `selfmail` CLI (plus an MCP server exposing a send_email tool).
---

# selfmail

[`selfmail`](https://github.com/alltuner/selfmail) sends an email to a pre-configured
"me" address with a single command, over [Resend](https://resend.com). It runs
anywhere — a laptop, a cron job, CI, a cloud runner, or an AI agent — with no GUI and
no local mail server. Reach for it whenever a task should end with "...and email it to
me."

## Invocation

Prefer an installed binary; otherwise run it straight from PyPI with `uvx`:

```bash
if command -v selfmail >/dev/null; then selfmail "$@"
else uvx selfmail "$@"; fi
```

## Configure (once)

```bash
selfmail init        # paste a Resend key (Sending access); it emails you a test
```

Or, for CI / headless / agents, skip the file and use environment variables:

```bash
export RESEND_API_KEY=re_...
export SELFMAIL_TO=you@example.com
export SELFMAIL_FROM=onboarding@resend.dev   # or you@yourdomain.com once verified
```

`selfmail doctor` reports what's configured without sending.

## Common usage

```bash
selfmail "deploy finished"                       # body only; subject defaults to a timestamp
selfmail -s "build" "all green on main"          # explicit subject
some-command 2>&1 | selfmail -s "cron output"    # body from stdin (pipe)
selfmail -s "reports" -a a.pdf -a b.csv "see attached"   # multiple attachments
selfmail --html "<h1>Shipped</h1>"               # HTML body
selfmail --to ops@example.com "heads up"         # one-off different recipient
```

## MCP server

For agents that speak the Model Context Protocol, run it as a server instead of
shelling out:

```bash
uvx --from 'selfmail[mcp]' selfmail mcp
```

It exposes one tool — `send_email(subject, body, to?, html?)` — using the same
configuration as the CLI.

## Exit codes

- `0` — sent.
- `1` — the send failed (network error, or Resend rejected the message).
- `2` — configuration or usage error (no key, missing recipient/sender, bad flag).

## Gotchas

- The recipient **defaults to the configured "me" address** — it's "email *myself*".
  Use `--to` for the rare one-off to someone else.
- There is **no default sender**; it comes from config (set by `init`, or
  `SELFMAIL_FROM`). Resend's shared `onboarding@resend.dev` only delivers to your own
  Resend account address — fine for self-email; verify a domain to email anyone else.
- A `403` with an "only delivers to your own address" hint means a sender ↔ account
  mismatch — set `--from` to a verified-domain address.
