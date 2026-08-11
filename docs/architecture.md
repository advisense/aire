# Architecture

Why the harness is shaped this way, so the reasoning survives the people who made it.

## The harness is a config, not a framework

Claude Code already provides the agent loop, permission enforcement, context
management, and extension points. Building a wrapper around the Agent SDK would mean
reimplementing those to gain programmatic control this project does not need, because
the primary mode is interactive: an analyst driving a target, iterating, following
hunches.

The SDK becomes worth it if the mode changes — batch-triaging a corpus in CI, running
this as a service, or orchestrating flows the interactive loop will not express. Until
then, every capability is a skill, a subagent, an MCP server, or a case directory.

## Three buckets, kept strictly separate

The single most useful line to draw early is between the three extension types.

**Skill = knowledge and methodology.** How to identify a primitive, how to structure a
protocol reversing pass, what a finding must contain. No new capability — just judgment
encoded once so it does not have to be re-derived per session. This is where most
extension should happen.

**Tool = an action or data source**, with a sharp sub-distinction: *stateless CLIs are
not tools here.* `tshark`, `openssl`, `strings`, `binwalk`, `yara`, `rizin -qc` take
input and return output with nothing carried forward. They run through Bash, with the
invocation documented in a skill.

MCP servers are reserved for **stateful, session-oriented** tools where the value is
holding context across calls: a running Frida session, an attached debugger, an angr
project mid-exploration, a live mitmproxy flow list, a browser with injected hooks.
Wrapping stateless commands in MCP adds bureaucracy without capability. See
`tools/README.md`.

**Subagent = a delegated context** with its own window, tool set, and prompt.

## Subagents are for context hygiene first

The obvious reason to use subagents is parallelism. In reverse engineering it is not
the main one.

RE produces enormous noisy intermediate output — disassembly dumps, hexdumps, full
packet lists, `strings` on a stripped 40MB binary. Landing that in the main context
degrades the whole session. A subagent tasked "read this pcap, tell me what protocols
and crypto are in play" burns its own context on the noise and returns a paragraph.
That alone justifies the roster in `.claude/agents/`.

Secondary benefits: **specialization** — a narrow agent with a constants table
preloaded behaves better than a generalist — and **parallel exploration** across
several artifacts or competing hypotheses.

**The constraint that shapes the roster:** subagents cannot share live state. None of
them can reach into the main session's attached debugger or running instrumentation.
So the division is:

- **Delegate** read-heavy, self-contained work: triage, identification, corpus sweeps,
  bundle searching.
- **Keep on the main thread** anything holding a live session: debugger,
  instrumentation, interactive proxy, browser.

Agents write bulk output to the case directory and return a path plus a summary, which
keeps the handoff cheap in both directions.

## The case directory is the real memory

RE is long, iterative, and outlives any single context window. `cases/<name>/` holds
the artifact, everything derived from it, the findings, and the working log. Context
compaction, session restarts, and subagent handoffs all become survivable because the
state lives on disk rather than in the conversation.

It also makes handoffs between main thread and subagents clean: both read and write
the same directory instead of passing large blobs through the delegation boundary.

## Isolation

Untrusted binaries and live targets do not belong on the analyst's host. The intended
substrate is a disposable container or VM with snapshot/restore and controlled egress,
with Claude Code running against a workspace mounted inside it.

Egress scoping is the mechanism that keeps "analyze this web app" from becoming
"contact arbitrary hosts". The `SCOPE.md` gate in every case is the procedural layer
above it; `.claude/settings.json` deny and ask rules are the layer below. All three
exist because each fails differently: a procedural gate fails to inattention, a
permission rule fails to a subprocess that bypasses the built-in tools, and network
egress control catches what both miss.

## Permission posture

`.claude/settings.json` is deny-first and deliberately conservative about anything that
generates traffic. Read-only local analysis commands are allowlisted, since prompting
on `file` and `strings` trains the analyst to approve reflexively — which is the real
risk that a permission policy is trying to avoid.

Personal widening belongs in `.claude/settings.local.json` (gitignored), never in the
shared file.

## Deliberate omissions

- **No orchestration layer.** Claude Code's delegation is sufficient; a scheduler on
  top would need maintaining and would fight the interactive loop.
- **No tool abstraction layer.** Skills document invocations directly. An abstraction
  over `tshark` and `rizin` would need updating every time either changes, in exchange
  for hiding syntax that is already documented upstream.
- **No exploitation tooling.** The deliverable of this harness is understanding and
  written findings. That boundary is stated in `CLAUDE.md` and reflected in the agent
  prompts.
- **Mobile is out of scope** for now. Adding it means a `mobile-re` skill and a
  session-oriented MCP server for on-device instrumentation; the structure already
  accommodates it.

## Extension order

When adding capability, try these in order and stop at the first that works:

1. A skill. Most needs are knowledge, not code.
2. A reference file under an existing skill, if it is a table or a playbook variant
   rather than a new methodology.
3. A subagent, once you have spawned the same kind of worker three times by hand.
4. An MCP server, only for genuinely stateful tools, and only after checking whether a
   community server already exists.
