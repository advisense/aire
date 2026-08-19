---
name: automatic-analysis
description: Run a case autonomously through every applicable corpus-backed weakness check and feasible test, without asking the user questions. Use only when the user explicitly requests automatic, autonomous, unattended, or no-questions analysis of an existing case.
argument-hint: cases/<case-name>
---

# Automatic analysis

Work autonomously on the existing case named in `$ARGUMENTS`. Do not ask the user
questions during this run. Continue until every selected corpus entry has a terminal
disposition or further progress is blocked by a boundary below.

Automatic mode changes interaction policy, not authorization or safety policy. It
does not authorize a live target, widen `SCOPE.md`, disclose secrets, install tools,
execute untrusted artifacts on the host, or bypass permission controls. Treat any
operation that requires interactive approval as blocked. Never invent missing scope,
credentials, facts, or evidence.

## Boundaries

Read `SCOPE.md` first. Local, read-only analysis may continue when live-target details
are incomplete. Perform a test that generates traffic, executes a sample, mutates a
target, or demonstrates impact only when that exact activity and target are explicitly
authorized in `SCOPE.md` and the required isolation is available.

When a test cannot be performed within those boundaries, do not ask for permission or
input. Exhaust safe alternatives, then record the affected corpus entry as `unknown`
with the exact test, prerequisite, and blocker. Missing optional software is handled
the same way after trying installed fallbacks; never install or download tooling.

Stop immediately only for a condition that makes all useful work unsafe or
unreliable, such as a missing case directory, missing `SCOPE.md`, corpus snapshot
drift, or evidence-integrity failure. Report the condition without asking a question.

## Autonomous loop

1. Read `SCOPE.md`, `ARTIFACTS.json`, `FINDINGS.md`, `EVIDENCE.jsonl`, `HYPOTHESES.md`,
   `DRAFT-FINDINGS.md`, recent `NOTES.md`, and any existing `CORPUS-COVERAGE.json`.
   Inventory the case artifacts and installed tools.
2. Identify the target's primitives, protocols, platforms, and threat model from case
   evidence. Use the relevant analysis skills. Prefer reproducible static and passive
   tests before dynamic or active ones.
3. Use the `corpus-lookup` skill to inspect all registered corpora and categories.
   Select every plausibly applicable slice; when applicability is uncertain, include
   rather than exclude it. Explicitly record every whole-corpus exclusion and reason.
   If a ledger already exists, keep its pinned selections and snapshots.
4. Work through `ledger next` batches of at most eight. For each entry:
   - apply its prerequisites to the target;
   - run every feasible check it specifies, plus the smallest useful follow-up tests;
   - record each located, reproducible result as an observation via
     `./tools/evidence add` (cite files, offsets, packet numbers, commands, or trace
     locations); capture interpretations and their falsification tests in
     `HYPOTHESES.md`;
   - set a terminal status using the `corpus-lookup` definitions;
   - record negative results and dead ends in `NOTES.md`.
5. Revisit `unknown` entries whenever later evidence or another safe test could resolve
   them. Do not leave an entry `unchecked` merely because a test failed or a fact was
   unavailable.
6. For each `confirmed` or `probable` weakness, draft a finding in `DRAFT-FINDINGS.md`
   citing the backing `O-NNN` observations, invoke `findings-reviewer`, reconcile its
   verdict, and promote only accepted findings to `FINDINGS.md`. Automatic mode permits this reconciliation
   without user input; the independent review gate still applies.
7. Run `ledger verify`. A successful run ends with zero `unchecked` and zero `unknown`
   entries. A bounded run may end with `unknown` entries only after all safe,
   authorized alternatives have been exhausted; in that case verification is expected
   to fail and the run must not be called complete.

## Final report

Return a compact report containing the selected corpora and pinned versions, status
counts, findings added or rejected, tests performed, excluded corpora with reasons,
unresolved items with their exact blockers and required tests, and the result of
`ledger verify`. Do not end with questions or requests for confirmation.
