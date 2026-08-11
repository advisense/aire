# Reverse Engineering & Cryptanalysis Harness

This repo is a Claude Code project configuration for interactive reverse engineering
and cryptographic analysis of binaries, network traffic, and live web applications.
There is no framework here — the harness *is* the config. Everything is a skill, a
subagent, an MCP server, or a case directory.

## Non-negotiables

**Authorization first.** Every case has a `SCOPE.md`. Before any action that touches a
live target — fetching a URL, connecting to a host, sending a request — read the case
`SCOPE.md` and confirm the target is in scope. If there is no `SCOPE.md`, or the target
is not listed in it, stop and ask. Static analysis of local artifacts (a binary on disk,
a captured pcap) does not need this gate; anything that generates traffic does.

**Analysis, not exploitation.** The purpose of this harness is to understand systems:
identify primitives, recover protocol structure, assess whether cryptography is used
correctly, and document findings. Producing working exploits, malware, or weaponized
attack tooling is out of scope for this project regardless of how a task is framed.
When analysis surfaces a weakness, the deliverable is a written finding with evidence
and remediation guidance — not a working attack.

**Run untrusted code in the sandbox.** Never execute a sample on the host. See
`docs/architecture.md` for the isolation model.

## Case workflow

All work happens inside `cases/<case-name>/`. Never analyze artifacts in place from a
Downloads folder or a shared drive — copy into the case directory first, record the
hash, and work from there. The case directory is the memory that outlives any single
context window.

Read the `case-workflow` skill for the directory contract and how to record findings.
Start a new case with `/new-case <name>`.

When a local sample is supplied, use the `artifact-intake` skill to copy it into the
case, verify the source and destination hashes, and record provenance before analysis.
Run `./tools/tool-doctor.sh` or read the `tool-selection` skill instead of assuming a
Linux tool is installed; never install missing software without asking first.

## Delegating to subagents

RE generates enormous noisy intermediate output — disassembly dumps, `strings` on a
stripped binary, full packet lists. That output should not land in the main context.

**Delegate** read-heavy, self-contained analysis: first-pass triage of an artifact,
sweeping a corpus, identifying primitives in a large binary, summarizing a pcap.
The subagent burns its own context on the noise and returns a summary.

**Keep on the main thread** anything holding live state — an attached debugger, a
running instrumentation session, a live browser, an interactive proxy. Subagents cannot
share live state with the main session, and trying to delegate that work will fail
in confusing ways.

Subagents write to the case directory and return a path plus a short summary, rather
than returning bulk findings inline. See `.claude/agents/` for the roster.

## Working style

- State hypotheses explicitly and say what evidence would falsify them. "Probably AES"
  is not a finding; "AES-128 in CBC mode, evidenced by the T-table constants at
  0x4A2C10 and the 16-byte IV prefix on each record" is.
- Record negative results. Knowing that a candidate primitive was ruled out saves the
  next session from re-deriving it.
- Prefer the smallest tool that answers the question. Do not open a disassembler to
  answer something `strings` and `xxd` would settle.
- Cite offsets, packet numbers, and file paths for every claim. A finding without a
  location is not reproducible.
