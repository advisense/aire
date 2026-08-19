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
  corpora/              Versioned, machine-queryable weakness corpora and registry
  skills/               Methodology — how to do the work
    case-workflow/      Case directory contract and finding format
    crypto-primitive-id/  Identifying primitives from constants and behaviour
    binary-recon/       Static and dynamic binary analysis
    traffic-analysis/   pcap and TLS-adjacent protocol work
    webapp-crypto/      Client-side crypto in live web applications
    artifact-intake/    Safe sample import, hashing, and provenance
    tls-certificate-analysis/  X.509, key container, and handshake inspection
    tool-selection/     Portable selection of installed local tools
    corpus-lookup/      Isolated corpus queries and exhaustive case coverage workflow
    automatic-analysis/  Unattended, no-questions corpus-backed case review
    new-case/           /new-case — scaffolds a case directory
  agents/               Delegated context — read-heavy triage workers
      findings-reviewer.md  Independent challenge of case findings and confidence ratings
      hypothesis-challenger.md  Bounded alternative-hypothesis synthesis
cases/                  One directory per target. Gitignored except TEMPLATE/
                        Layered memory: ARTIFACTS.json → EVIDENCE.jsonl (O-NNN) →
                        HYPOTHESES.md → FINDINGS.md; EVIDENCE trusted over NOTES.md
tools/                  Stateless helpers and local MCP servers (see tools/README.md)
    corpus-lookup       Corpus queries + case coverage ledger
    evidence            Manage a case's EVIDENCE.jsonl observations
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

List the installed weakness corpora without loading their contents into context:

```bash
./tools/corpus-lookup corpora
```

To run an existing, scoped case through every applicable corpus check without
interactive questions:

```text
/automatic-analysis cases/acme-firmware
```

Automatic mode runs all feasible local and explicitly authorized tests. Missing scope,
credentials, isolation, or tooling is recorded as an unresolved blocker; it is never
treated as permission to widen the assessment. A read-only reasoning challenger runs
when unexplained behavior materially steers the analysis and once before reporting. Its
suggestions remain subject to the same scope and evidence rules, and residual behavior
is reported separately from corpus-ledger completeness.

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
