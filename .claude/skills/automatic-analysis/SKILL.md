---
name: automatic-analysis
description: Run a case autonomously through every applicable corpus-backed weakness check and feasible test, without asking the user questions. Use only when the user explicitly requests automatic, autonomous, unattended, or no-questions analysis of an existing case.
argument-hint: cases/<case-name>
---

# Automatic analysis

Work autonomously on the case named in `$ARGUMENTS`. Ask no questions during the run.
Continue until every selected corpus entry has a terminal disposition or a boundary below
blocks progress.

Automatic mode changes interaction policy, not authorization or safety policy. It does not
authorize a live target, widen `SCOPE.md`, disclose secrets, install tools, execute
untrusted artifacts on the host, or bypass permission controls. Anything requiring
interactive approval is blocked. Never invent missing scope, credentials, facts, or
evidence.

## Boundaries

Read `SCOPE.md` first. Local read-only analysis may continue when live-target details are
incomplete. Run a test that generates traffic, executes a sample, mutates a target, or
demonstrates impact only when that exact activity and target are explicitly authorized in
`SCOPE.md` and the required isolation exists.

When a test falls outside those boundaries, do not ask. Exhaust the safe alternatives,
then record the entry as `unknown` with the exact test, prerequisite, and blocker. Handle
missing optional software the same way after trying installed fallbacks. Never install or
download tooling.

Stop only for a condition that makes all useful work unsafe or unreliable: missing case
directory, missing `SCOPE.md`, corpus snapshot drift, or evidence-integrity failure.
Report it without asking a question.

## Autonomous loop

1. Read `SCOPE.md`, `ARTIFACTS.json`, `FINDINGS.md`, `EVIDENCE.jsonl`, `HYPOTHESES.md`,
   `DRAFT-FINDINGS.md`, recent `NOTES.md`, and any existing `CORPUS-COVERAGE.json`.
   Inventory the case artifacts and installed tools.
2. Identify the target's primitives, protocols, platforms, and threat model from case
   evidence, using the relevant analysis skills. Prefer reproducible static and passive
   tests before dynamic or active ones.
3. Use `corpus-lookup` to inspect all registered corpora and categories. Select every
   plausibly applicable slice; when applicability is uncertain, include rather than
   exclude. Record every whole-corpus exclusion and its reason. An existing ledger keeps
   its pinned selections and snapshots.
4. Work `ledger next` batches of at most eight. Per entry: apply its prerequisites to the
   target; run every feasible check it specifies plus the smallest useful follow-ups;
   record each located, reproducible result via `./tools/evidence add`, citing files,
   offsets, packet numbers, commands, or trace locations; put interpretations and their
   falsification tests in `HYPOTHESES.md`; set a terminal status per the `corpus-lookup`
   definitions; log negative results and dead ends in `NOTES.md`.
5. Revisit `unknown` entries whenever later evidence or another safe test could resolve
   them. Never leave an entry `unchecked` because a test failed or a fact was unavailable.
6. For each `confirmed` or `probable` weakness, draft a finding in `DRAFT-FINDINGS.md`
   citing its `O-NNN` observations, invoke `findings-reviewer`, reconcile the verdict, and
   promote only accepted findings. Automatic mode permits reconciliation without user
   input; the independent review gate still applies.
7. Invoke `hypothesis-challenger` once after ledger work and finding reconciliation,
   before the final report: give it the case path and ask for a residual-uncertainty
   review. If it names one safe, authorized, proportionate test with material information
   gain, run it and update evidence, hypotheses, ledger, and affected findings through
   their normal gates. Do not re-invoke when that cycle produces no materially new
   verified evidence.
8. Run `ledger verify`. A successful run ends with zero `unchecked` and zero `unknown`
   entries. A bounded run may end with `unknown` entries only after all safe, authorized
   alternatives are exhausted; verification is then expected to fail and the run must not
   be called complete.

## Bounded hypothesis challenge

Mid-run, invoke `hypothesis-challenger` before broadening or escalating testing only when
an unexplained anomaly is materially steering the analysis and at least one holds:

- verified observations conflict with the current working model;
- the behavior changes corpus applicability, the threat model, a likely finding, or which
  test branch runs next;
- two focused tests have failed to discriminate the same alternatives; or
- the next step would repeat or substantially escalate a dead end in `NOTES.md`.

Do not invoke it for an ordinary corpus `unknown` with a clear scope, tooling, data, or
isolation blocker; a single negative test; a low-impact curiosity that cannot affect
coverage or findings; or an anomaly already challenged without materially new verified
evidence.

Identify an invocation by its anomaly cluster and evidence state. Invoke at most once per
pair, and re-invoke only after a new verified observation, a supersession or
contradiction, or a material hypothesis-status change. Budget: two mid-run invocations
plus the mandatory pre-report one. Once exhausted, preserve the behavior as an open
hypothesis or residual uncertainty rather than expanding the analysis indefinitely.

The challenger is advisory and read-only. Assess its suggestions against `SCOPE.md`,
safety, expected information gain, and cost; run at most the smallest feasible high-value
test; record resulting facts through `./tools/evidence`; update `HYPOTHESES.md`; revisit
affected ledger entries. Log the invocation reason, evidence state, accepted or rejected
suggestion, and stop condition in `NOTES.md`. Unsafe, unauthorized, duplicative, or
disproportionate suggestions are blockers or dead ends, not tests.

## Final report

Return a compact report: selected corpora and pinned versions, status counts, findings
added or rejected, tests performed, excluded corpora with reasons, unresolved items with
their exact blockers and required tests, and the `ledger verify` result. State whether
`hypothesis-challenger` ran, which anomaly clusters it challenged, which suggestions were
accepted or rejected, and any residual unexplained behavior or open hypotheses. Corpus
verification does not mean the target is fully explained; report those states separately.
Do not end with questions or requests for confirmation.
