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

For a comprehensive cryptographic, TLS, protocol, implementation, or side-channel
weakness assessment, use the `corpus-lookup` skill. Select and preview the applicable
versioned corpora, then maintain `cases/<case>/CORPUS-COVERAGE.json` through
`./tools/corpus-lookup`; do not read corpus JSONL files directly or hand-edit the
ledger. Never describe corpus coverage as complete unless `ledger verify` passes, and
state the pinned corpus versions, selected categories, and any excluded corpora. The
skill runs the lookup or multi-batch review in its own isolated context and returns a
compact result to the main session.

## Delegating to subagents

RE generates enormous noisy intermediate output — disassembly dumps, `strings` on a
stripped binary, full packet lists. That output should not land in the main context.

**Delegate** read-heavy, self-contained analysis: first-pass triage of an artifact,
sweeping a corpus, identifying primitives in a large binary, summarizing a pcap.
The subagent burns its own context on the noise and returns a summary.

**Never write a finding to `FINDINGS.md` until the `findings-reviewer` has reviewed
it.** The sequence is: (1) draft the finding and its cited evidence in
`DRAFT-FINDINGS.md`, (2) delegate the draft to `findings-reviewer`, (3) read the
reviewer's verdict, (4) reconcile by hand — accept, revise, or reject, (5) only then
move the accepted finding from `DRAFT-FINDINGS.md` to `FINDINGS.md` and preserve the
returned `REVIEW.md` content. Writing to `FINDINGS.md` before step 2 is a workflow
violation. The reviewer is deliberately read-only so it contests findings instead of
fixing them.

**Keep on the main thread** anything holding live state — an attached debugger, a
running instrumentation session, a live browser, an interactive proxy. Subagents cannot
share live state with the main session, and trying to delegate that work will fail
in confusing ways.

Subagents normally write to the case directory and return a path plus a short summary,
rather than returning bulk findings inline. The findings reviewer is the read-only
exception. See `.claude/agents/` for the roster.

## Working style

- Be terse. Keep updates and final responses brief, reporting only decisions, essential
  evidence, blockers, and next actions. Do not narrate routine tool use.
- State hypotheses explicitly and say what evidence would falsify them. "Probably AES"
  is not a finding; "AES-128 in CBC mode, evidenced by the T-table constants at
  0x4A2C10 and the 16-byte IV prefix on each record" is.
- Record negative results. Knowing that a candidate primitive was ruled out saves the
  next session from re-deriving it.
- Prefer the smallest tool that answers the question. Do not open a disassembler to
  answer something `strings` and `xxd` would settle.
- Cite offsets, packet numbers, and file paths for every claim. A finding without a
  location is not reproducible.
- When stuck — a tool fails, an approach dead-ends, or evidence is ambiguous — do not
  stop. State why the current path is blocked, generate at least two alternative
  hypotheses or approaches, and pursue the most promising one. Record the dead end so
  it is not revisited.
