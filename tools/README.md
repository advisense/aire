# Local MCP servers

This directory has three deliberately stateless helpers. `tool-doctor.sh` reports which
documented CLI capabilities are available without installing anything:

```bash
./tools/tool-doctor.sh
```

`corpus-lookup` performs bounded, paginated queries over registered weakness corpora
and maintains version- and content-pinned case coverage ledgers:

```bash
./tools/corpus-lookup corpora
./tools/corpus-lookup search "GCM nonce reuse" --limit 10
```

`evidence` manages a case's `EVIDENCE.jsonl` — the layer of atomic, located,
reproducible observations (`O-NNN`) that findings cite. It allocates IDs, records
supersession and contradictions, and validates the file; it never executes an
observation's `reproduce` command (verification is a human act). The case is identified
by its `SCOPE.md`, as with `corpus-lookup`:

```bash
./tools/evidence add cases/acme-firmware \
  --artifact artifacts/fw.bin --location "file offset 0x4A2C10" \
  --observed "Bytes match the AES forward S-box." \
  --reproduce "xxd -s 0x4A2C10 -l 256 artifacts/fw.bin"
./tools/evidence list cases/acme-firmware
./tools/evidence validate cases/acme-firmware
```

Everything else in this directory should follow the stateful-server rule below.

This directory holds MCP servers for **stateful** tools — the ones whose value is
holding a live session across multiple calls. Register them in `.mcp.json` at the repo
root, or scope them to a single subagent with the `mcpServers` frontmatter field so
their tool descriptions never consume main-conversation context.

## What belongs here

A tool earns an MCP server when the session *is* the state:

- **Instrumentation** (Frida) — attach once, then hook, read memory, and call
  functions across many turns.
- **Debugger** (gdb/pwndbg, lldb) — breakpoints, stepping, and register reads against
  a single attached process.
- **Symbolic execution** (angr) — a project and its exploration state are expensive to
  rebuild per call.
- **Interactive proxy** (mitmproxy) — a live flow list that accumulates as traffic
  arrives.
- **Browser** (Playwright/CDP) — page state, cookies, and injected hooks that must
  persist between calls.

## What does not belong here

Stateless CLIs. `tshark`, `openssl`, `strings`, `xxd`, `binwalk`, `yara`, and
`rizin -qc` all take input and return output with nothing to carry forward. Wrapping
them in MCP adds a layer without adding capability. Document the invocation in the
relevant skill and let Bash run them — that is the difference between a minimal
harness and a bureaucratic one.

## Before writing one

Check whether it already exists. There are community MCP servers for rizin/radare2 and
Ghidra headless, among others. Integration beats implementation.

## Design notes

Keep the tool surface small — a handful of well-named operations beats a wrapper around
every API method, since every tool description costs context in whatever agent can see
it. Return summaries rather than dumps, and write bulk output to the case directory
with a path in the response. Servers should fail loudly when no session is attached
rather than silently starting one.
