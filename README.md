# aire

A minimal, extendable Claude Code project config for interactive reverse engineering
and cryptographic analysis — binaries, network traffic, and live web applications.

It is deliberately not a framework. Claude Code already provides the agent loop,
permissioning, and context management; this repo supplies the domain knowledge,
delegation roster, and working conventions on top of it.

## Layout

```
CLAUDE.md               House rules: authorization, case workflow, delegation policy
.claude/
  settings.json         Permission rules (deny-first), shared with the team
  skills/               Methodology — how to do the work
    case-workflow/      Case directory contract and finding format
    crypto-primitive-id/  Identifying primitives from constants and behaviour
    binary-recon/       Static and dynamic binary analysis
    traffic-analysis/   pcap and TLS-adjacent protocol work
    webapp-crypto/      Client-side crypto in live web applications
    artifact-intake/    Safe sample import, hashing, and provenance
    tls-certificate-analysis/  X.509, key container, and handshake inspection
    tool-selection/     Portable selection of installed local tools
    new-case/           /new-case — scaffolds a case directory
  agents/               Delegated context — read-heavy triage workers
cases/                  One directory per target. Gitignored except TEMPLATE/
tools/                  Local MCP servers for stateful sessions (see tools/README.md)
docs/architecture.md    Why the harness is shaped this way
```

## Getting started

```bash
git clone <this repo> && cd aire
claude
```

Then:

```
/new-case acme-firmware
```

Fill in `cases/acme-firmware/SCOPE.md` before touching anything live.

Check which local analysis capabilities are available:

```bash
./tools/tool-doctor.sh
```

The starter configuration works with the stock macOS command-line tools and uses
installed Wireshark, OpenSSL, mitmproxy, and Docker capabilities when present.
Specialist tools such as Rizin, binwalk, YARA, Frida, and Ghidra remain optional; the
skills ask before recommending an installation.

## Extending it

The extension points are the standard Claude Code ones, in rough order of how often
you should reach for them:

1. **Add a skill** — a new `SKILL.md` under `.claude/skills/`. This is the default.
   Most new capability is knowledge, not code: a playbook for a protocol family, a
   constants table, a house convention.
2. **Add a subagent** — a new file in `.claude/agents/`, when you find yourself
   repeatedly spawning the same kind of worker with the same instructions.
3. **Add an MCP server** — only for *stateful* tools that hold a session across calls.
   Stateless CLIs (`tshark`, `openssl`, `strings`, `radare2 -qc`) do not need one;
   document the invocation in a skill and let Bash handle it. See `tools/README.md`.

Skills and agents are picked up from disk within a few seconds; no restart needed
unless you just created the `skills/` or `agents/` directory itself.
