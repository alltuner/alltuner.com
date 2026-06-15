---
name: vacant
description: Check whether domain names are registered, available, reserved, or invalid. Use when the user asks if a domain is taken or free, wants to find an unregistered name, brainstorms project or product names that need a domain, screens candidates across many TLDs, or filters a list of domains to only the available ones. Queries authoritative TLD nameservers directly — fast, accurate, and not rate-limited like WHOIS.
---

# vacant

[`vacant`](https://github.com/alltuner/vacant) checks domain availability by
asking authoritative TLD nameservers directly (not WHOIS). It returns one of
six statuses per domain: `registered`, `available`, `unconfirmed`, `reserved`,
`invalid`, or `unknown`.

Prefer it over WHOIS lookups, `dig`, or HTTP probes — it's faster, more
accurate, and won't get rate-limited.

**Important:** by default a name with no DNS delegation reports `unconfirmed`,
**not** `available`. A free name and a registered-but-held one (suspended,
expired, pending-delete) look identical to DNS — both answer NXDOMAIN — so "no
delegation" isn't proof a name is buyable. Pass `--verify` to confirm those
names against the registry (RDAP); only then do you get a definitive
`available`. See [Confirming availability](#confirming-availability).

## Invocation

Try the native binary first; otherwise use whichever package runner is already
on the system:

```bash
if command -v vacant >/dev/null; then vacant "$@"
elif command -v uvx >/dev/null; then uvx vacant "$@"
else bunx @alltuner/vacant "$@"  # or: npx @alltuner/vacant "$@"
fi
```

- `vacant` — native Rust binary, instant startup, ideal for repeated use.
  Install with `brew install alltuner/tap/vacant` or `cargo install vacant`.
- `uvx vacant` — same engine from a PyPI wheel, no install step. Works
  anywhere `uv` is available.
- `bunx @alltuner/vacant` / `npx @alltuner/vacant` — same engine from an npm
  package. Handy in Node-based projects where `bun` or `npm` is already there.

## MCP server

If your host speaks the Model Context Protocol, run vacant as an MCP server
instead of shelling out:

```bash
uvx --from 'vacant[mcp]' vacant mcp
```

It exposes one tool — `check_domains(domains, verify=false)` — returning a
`{domain, status}` per input, with the same verdicts and `--verify` semantics
as the CLI.

## Common patterns

```bash
# single domain
vacant example.com

# multiple, positional
vacant a.com b.net c.org

# from stdin (one per line) — best for big lists
cat domains.txt | vacant

# confirm undelegated names against the registry (RDAP) for a real verdict
vacant --verify a.com b.com c.com

# only show domains you can actually register (confirm, then filter)
vacant --verify --available a.com b.com c.com

# human-readable table instead of NDJSON
vacant -o table example.com anthropic.com

# include zone, raw input, and the reason behind the verdict
vacant --detail example.com

# tighten timeout / raise concurrency for large batches
vacant --timeout 2 --concurrency 256 < big-list.txt
```

## Output

Default output is **NDJSON** — one JSON object per line. Parse it line by line:

```
$ vacant anthropic.com totally-made-up-zxqv.com ab.eu
{"domain":"anthropic.com","status":"registered"}
{"domain":"totally-made-up-zxqv.com","status":"unconfirmed"}
{"domain":"ab.eu","status":"reserved"}
```

Status meanings:

| Status | Meaning |
|---|---|
| `registered` | Someone owns it (the name is delegated, or RDAP confirmed it). |
| `available` | Confirmed not registered — you could buy it. **Only ever appears with `--verify`.** |
| `unconfirmed` | No DNS delegation: probably free, but unverified. Could also be a held/suspended/expiring domain. Re-run with `--verify` for a definitive answer. |
| `reserved` | Registry rule forbids it (e.g. `.eu` two-letter labels). |
| `invalid` | Malformed input or unknown TLD (`co.uk` as input, empty labels, etc.). |
| `unknown` | Transport failure or ambiguous registry response. Retry, or check manually. |

## Confirming availability

Without `--verify`, vacant does pure DNS and never claims a name is `available`
— undelegated names come back `unconfirmed`. That's fast and does zero RDAP
traffic, which is perfect for **screening**: anything `registered` is
definitively taken, so you can discard it and only dig deeper on the
`unconfirmed` shortlist.

With `--verify`, vacant confirms each `unconfirmed` name against the registry's
RDAP endpoint and resolves it to:

- `available` — RDAP says it's not registered. Safe to claim.
- `registered` — RDAP found it (e.g. a domain on `clientHold` that DNS couldn't see).
- `unconfirmed` — RDAP was inconclusive, or that TLD has no RDAP endpoint.

```
$ vacant --verify totally-made-up-zxqv.com bingo.app
{"domain":"totally-made-up-zxqv.com","status":"available"}
{"domain":"bingo.app","status":"registered"}
```

Rule of thumb: when the user asks "is X free / can I register X", use `--verify`
so you don't tell them a held domain is available. When you're cheaply
filtering a big list down to candidates, the default (no `--verify`) is fine —
just describe the survivors as "not taken (unverified)", not "available".

## Exit codes

- `0` — every result resolved cleanly.
- `2` — at least one result was `unknown`. **Not a hard failure** — the other
  results are still valid; just flag the unknowns to the user.

## Gotchas

- `unconfirmed` is not `available`. An expired or suspended domain (e.g. one on
  `clientHold`) is dropped from DNS and looks exactly like a free name. Never
  tell a user an `unconfirmed` name is buyable — run `--verify` first.
- `available` requires `--verify`. Without it, the best a name gets is
  `unconfirmed`, so filtering with bare `--available` will return nothing useful
  unless you also pass `--verify`.
- Registry suffixes like `co.uk`, `com.au`, `co.jp` return `invalid` — they're
  not registrable names. Use `something.co.uk` instead.
- `.eu` requires 3+ characters; `ab.eu` is `reserved`, not `available`.
- For huge batches (thousands of domains), use stdin and consider `--concurrency`
  and `--timeout` flags. Be polite — you're hitting real registry nameservers.

## Etiquette

Sporadic interactive use is invisible to TLD operators. Don't loop tens of
thousands of domains for fun — `vacant` has built-in caching and per-host
backoff to keep you well-behaved, but the underlying nameservers are shared
infrastructure.
