# Architecture

Why the harness is shaped this way, so the reasoning survives the people who made it.

## The harness is a config, not a framework

Claude Code already provides the agent loop, permission enforcement, context management,
and extension points. Wrapping the Agent SDK would mean reimplementing those for
programmatic control this project does not need. The default mode is interactive: an
analyst drives a target, iterates, and follows hunches. The opt-in `automatic-analysis`
skill uses the same loop to exhaust a case's applicable corpus checks without
conversational pauses.

The SDK becomes worth it for non-conversational execution: batch triage in CI, running
this as a service, or orchestration the agent loop will not express. Until then, every
capability is a skill, a subagent, an MCP server, or a case directory.

## Interactive and automatic analysis

Interactive analysis may stop for choices, missing facts, or permission. Automatic
analysis instead makes conservative choices, runs every feasible test the selected corpora
indicate, and records unresolved checks with exact blockers. It never converts silence
into authorization: `SCOPE.md`, host isolation, permission rules, and the findings-review
gate are unchanged. Unattended coverage stays reproducible, and an incomplete run stays
visibly incomplete.

## Three buckets, kept strictly separate

**Skill = knowledge and methodology.** How to identify a primitive, how to structure a
protocol reversing pass, what a finding must contain. No new capability, just judgment
encoded once instead of re-derived every session. Most extension belongs here.

**Tool = an action or data source**, with a sharp sub-distinction: stateless CLIs are not
tools here. `tshark`, `openssl`, `strings`, `binwalk`, `yara`, and `rizin -qc` take input
and return output with nothing carried forward. They run through Bash, with the invocation
documented in a skill. MCP servers are reserved for **stateful, session-oriented** tools
whose value is holding context across calls: a running Frida session, an attached
debugger, an angr project mid-exploration, a live mitmproxy flow list, a browser with
injected hooks. Wrapping stateless commands in MCP adds bureaucracy without capability.
See `tools/README.md`.

**Subagent = a delegated context** with its own window, tool set, and prompt.

## Subagents are for context hygiene first

The obvious reason to use subagents is parallelism. In reverse engineering that is not the
main one. RE produces enormous noisy output: disassembly dumps, hexdumps, full packet
lists, `strings` on a stripped 40MB binary. Landing that in the main context degrades the
whole session. A subagent tasked with "read this pcap, tell me what protocols and crypto
are in play" spends its own context on the noise and returns a paragraph. That alone
justifies the roster in `.claude/agents/`. Specialization and parallel exploration are
secondary benefits.

Independent review depends on the same isolation. A findings reviewer starts from the case
evidence without inheriting the analyst's conversation, so it re-derives claims instead of
absorbing the framing that produced them.

The hypothesis challenger uses that isolation differently. It runs before closure to
generate competing explanations for unresolved behavior and propose the smallest
discriminating test. Automatic analysis invokes it when contradictory or non-discriminating
evidence controls the next branch, and once before final reporting. It is not periodic:
challenges are deduplicated by anomaly and evidence state, and capped so speculative
synthesis cannot become its own rabbit hole. The findings reviewer remains the later gate
over drafted conclusions, confidence, and omissions.

**The constraint that shapes the roster:** subagents cannot share live state. None can
reach into the main session's attached debugger or running instrumentation. So:

- Delegate read-heavy, self-contained work: triage, identification, corpus sweeps, bundle
  searching, read-only hypothesis challenges.
- Keep on the main thread anything holding a live session: debugger, instrumentation,
  interactive proxy, browser. The main thread also owns authorization, test execution,
  evidence recording, and all durable case changes.

Agents write bulk output to the case directory and return a path plus a summary, which
keeps the handoff cheap in both directions.

## The case directory is the real memory

RE outlives any single context window. `cases/<name>/` holds the artifact, everything
derived from it, the findings, and the working log, so compaction, session restarts, and
subagent handoffs become survivable.

That memory is layered by how much it can be trusted, so a mis-recorded detail cannot
silently harden into an unquestioned fact. `ARTIFACTS.json` fixes identity and provenance.
`EVIDENCE.jsonl` holds atomic, located, reproducible observations (`O-NNN`, managed by
`tools/evidence`): what was *seen*, never what it means, superseded rather than edited so
corrections keep their history. `HYPOTHESES.md` holds the interpretations of those
observations with the tests that would falsify them. `FINDINGS.md` holds only reviewed
conclusions, each citing the observations behind it. `NOTES.md` is narrative and never
authoritative: the main thread trusts `EVIDENCE.jsonl` over it and re-runs any observation
before building a finding on it.

The layering also keeps handoffs clean. Main thread and subagents read and write the same
directory instead of passing large blobs across the delegation boundary.

## Corpora are queried, not loaded

Large weakness catalogs live under `.claude/corpora/` as versioned JSONL snapshots. The
forked `corpus-lookup` skill owns the lookup and audit workflow in an isolated context;
the stateless `tools/corpus-lookup` helper performs capped search, detail retrieval,
pagination, and ledger updates. Only the compact result returns to the main conversation.

An exhaustive review is defined by a case's generated `CORPUS-COVERAGE.json`. It pins
corpus versions, content digests, and selected categories, then assigns every selected
entry an evidence-backed disposition. Verification recomputes the selected entry set, so
completeness stays reproducible without pretending the catalog covers weaknesses published
after its snapshot date.

## Isolation

Untrusted binaries and live targets do not belong on the analyst's host. The intended
substrate is a disposable container or VM with snapshot/restore and controlled egress, with
Claude Code running against a workspace mounted inside it.

Egress scoping keeps "analyze this web app" from becoming "contact arbitrary hosts". The
`SCOPE.md` gate in every case is the procedural layer above it, `.claude/settings.json`
deny rules are the layer below, and egress control catches subprocess traffic that bypasses
the built-in tools.

## Permission posture

`.claude/settings.json` denies access to sensitive local data and pushing Git changes.
Analysis commands, including ones that generate traffic, are allowlisted; the mandatory
`SCOPE.md` check remains the authorization gate for live targets. Personal changes belong
in `.claude/settings.local.json` (gitignored), never in the shared file.

## Deliberate omissions

- **No orchestration layer.** Claude Code's delegation is sufficient. A scheduler on top
  would need maintaining and would fight the interactive loop.
- **No tool abstraction layer.** Skills document invocations directly. An abstraction over
  `tshark` and `rizin` would need updating every time either changes, in exchange for
  hiding syntax already documented upstream.
- **Mobile is out of scope** for now. Adding it means a `mobile-re` skill and a
  session-oriented MCP server for on-device instrumentation, which the structure already
  accommodates.

## Extension order

When adding capability, stop at the first that works:

1. A skill. Most needs are knowledge, not code.
2. A reference file under an existing skill, if it is a table or a playbook variant rather
   than a new methodology.
3. A subagent, once you have spawned the same kind of worker three times by hand.
4. An MCP server, only for genuinely stateful tools, and only after checking whether a
   community server already exists.
