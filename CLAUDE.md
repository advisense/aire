# Reverse Engineering & Cryptanalysis Harness

Claude Code config for interactive reverse engineering and cryptographic analysis of
binaries, network traffic, and web applications. Every capability is a skill, a subagent,
an MCP server, or a case directory. There is no framework.

## Non-negotiables

**Authorization first.** Before anything that touches a live target (fetching a URL,
connecting to a host, sending a request), read the case `SCOPE.md` and confirm the target
is listed. If it is not, or there is no `SCOPE.md`, stop and ask. Static analysis of local
artifacts needs no gate; anything that generates traffic does.

**Run untrusted code in the sandbox**, never on the host. Isolation model:
`docs/architecture.md`.

## Case workflow

Work happens in `cases/<case-name>/`, the memory that outlives a context window. Never
analyze an artifact in place: copy it in, record the hash, work from there. Start with
`/new-case <name>`. The `case-workflow` skill holds the directory contract and the finding
format.

Case memory is layered by trust. Observations (`EVIDENCE.jsonl`, one `O-NNN` per line,
managed with `./tools/evidence`) sit below hypotheses (`HYPOTHESES.md`, interpretations
plus their falsification tests), which sit below reviewed findings (`FINDINGS.md`, citing
observation IDs). `EVIDENCE.jsonl` outranks `NOTES.md`. Re-run any observation before it
becomes a finding's premise. "AES S-box bytes at 0x4A2C10" is an observation; "the program
implements AES" is a hypothesis until reachability is shown.

Skills to reach for:

- `artifact-intake` for every supplied sample, before analysis. It copies the file in,
  verifies hashes, and records provenance in `ARTIFACTS.json`.
- `tool-selection` or `./tools/tool-doctor.sh` instead of assuming a tool is installed.
  Never install software without asking.
- `corpus-lookup` for any comprehensive cryptographic, TLS, protocol, implementation, or
  side-channel assessment. Preview and select the applicable versioned corpora, then
  maintain `cases/<case>/CORPUS-COVERAGE.json` through `./tools/corpus-lookup`. Never read
  corpus JSONL directly or hand-edit the ledger. Coverage is complete only when
  `ledger verify` passes; state the pinned versions, categories, and exclusions.
- `automatic-analysis` only on an explicit request for automatic, autonomous, unattended,
  or no-questions review. It changes interaction policy and nothing else: absent
  authorization, credentials, isolation, or tooling become blockers and `unknown` coverage.

## Delegating to subagents

RE output is noisy: disassembly dumps, `strings` on a stripped binary, full packet lists.
Keep it out of the main context.

Delegate read-heavy, self-contained analysis: triage, corpus sweeps, primitive
identification in a large binary, pcap summaries. The subagent spends its own context on
the noise and returns a summary.

Never write to `FINDINGS.md` until `findings-reviewer` has reviewed. (1) Draft in
`DRAFT-FINDINGS.md`, citing the backing `O-NNN` observations. (2) Delegate to
`findings-reviewer`. (3) Read the verdict. (4) Reconcile by hand: accept, revise, or
reject. (5) Move accepted findings to `FINDINGS.md` and preserve the returned `REVIEW.md`.
Writing before step 2 is a workflow violation. The reviewer is read-only by design, so it
contests findings instead of fixing them.

Keep on the main thread anything holding live state: debugger, instrumentation, browser,
interactive proxy. Subagents cannot share it, and delegating that work fails confusingly.

Use `hypothesis-challenger` as a read-only, fresh-context pass when verified observations
conflict, when unexplained behavior is steering expensive analysis, or when an automatic
run is ready to report. It proposes competing explanations and discriminating tests. Scope
and safety checks, test execution, case-file mutation, evidence recording, and hypothesis
status stay with the main thread. It complements `findings-reviewer` rather than replacing
it.

Subagents write bulk output to the case directory and return a path plus a short summary.
`findings-reviewer` is the read-only exception. Roster: `.claude/agents/`.

## Working style

- Be terse: decisions, essential evidence, blockers, next actions. Do not narrate routine
  tool use.
- Cite offsets, packet numbers, and file paths for every claim. A finding without a
  location is not reproducible.
- State assumptions explicitly, keep them separate from verified observations, and say
  which conclusions depend on them.
- State hypotheses with what would falsify them. "Probably AES" is not a finding.
  "AES-128-CBC, evidenced by the T-tables at 0x4A2C10 and the 16-byte IV prefix on each
  record" is.
- Compute, do not infer: count the bytes in `abad1dea` with
  `echo -n 'abad1dea' | wc -c | awk '{print $1 / 2}'`.
- Use the smallest tool that answers the question. Do not open a disassembler for what
  `strings` and `xxd` settle.
- Record negative results. A ruled-out primitive saves the next session from re-deriving
  it.
- Keep a todo list for multi-step work. Mark tasks complete only when verified, and make
  blockers explicit.
- Use WebSearch when a conclusion depends on current external facts: disclosures,
  advisories, tool documentation, standards, unfamiliar technology. Prefer primary sources
  and cite URLs. Do not search for what local artifacts or pinned corpora settle. Never put
  secrets or case data in a query. WebSearch does not authorize contacting a target.
- When stuck, do not stop. Say why the path is blocked, generate at least two
  alternatives, pursue the most promising, and record the dead end.
