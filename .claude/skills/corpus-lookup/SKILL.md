---
name: corpus-lookup
description: Query versioned security weakness corpora in an isolated context and maintain an exhaustive per-case coverage ledger. Use when auditing cryptography, TLS, protocols, implementations, or side channels; checking every applicable weakness; looking up a weakness by concept or ID; or creating, continuing, or reporting corpus-backed case coverage.
argument-hint: [case path or lookup question]
context: fork
agent: general-purpose
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(./tools/corpus-lookup *)
---

# Corpus lookup

Perform this task in the isolated context:

> $ARGUMENTS

Use `./tools/corpus-lookup` and never read corpus JSONL files directly. The command caps
and paginates output so only the current batch enters context. Do not contact live
targets, execute untrusted artifacts, modify `FINDINGS.md`, or hand-edit a coverage
ledger.

## Direct lookup

Use the smallest operation that answers the question:

```bash
./tools/corpus-lookup corpora
./tools/corpus-lookup categories --corpus crypto-core
./tools/corpus-lookup search "GCM nonce reuse" --limit 10
./tools/corpus-lookup list --corpus crypto-core --category aead --limit 20
./tools/corpus-lookup show crypto-core:SYM-006
```

Follow the `next:` cursor from `list`; do not raise limits to load a corpus. Return only
the relevant entries, and never claim exhaustive coverage from a search.

## Case audit

1. Read `SCOPE.md`, `FINDINGS.md`, and recent `NOTES.md`.
2. Inspect `corpora` and `categories`. Include every slice applicable to the target's
   primitives, protocols, platforms, and threat model. Justify whole-corpus exclusions
   explicitly.
3. Preview before creating a ledger. A selection is a corpus, one category, or a
   category intersection using `+`:

   ```bash
   ./tools/corpus-lookup preview \
     --select crypto-core:aead --select crypto-core:rsa+side-channel
   ```

4. With no ledger, initialize from the previewed selections:

   ```bash
   ./tools/corpus-lookup ledger init cases/<case> \
     --select crypto-core --select tls-pki:certificate-validation
   ```

   With one, continue its pinned selections. Never replace or widen it silently; stop and
   report version drift.
5. Evaluate batches of at most eight:

   ```bash
   ./tools/corpus-lookup ledger next cases/<case> --limit 8
   ./tools/corpus-lookup ledger set cases/<case> crypto-core:SYM-006 \
     --status ruled-out --evidence "Unique nonce generated at src/aead.c:84"
   ```

6. Repeat until no unchecked entries remain, then run `ledger verify`.

Use these statuses precisely:

- `confirmed`: target evidence demonstrates the weakness.
- `probable`: strong evidence exists but confirmation is incomplete.
- `ruled-out`: target evidence demonstrates absence.
- `not-applicable`: prerequisites are demonstrably absent.
- `unknown`: applicable, but available evidence cannot decide it.
- `unchecked`: not evaluated; never a completed result.

Never use `ruled-out` merely because evidence was not found. If resolution needs live
traffic or executing an untrusted artifact, use `unknown` and name the exact test the
main session must run.

Return a compact summary: pinned versions and selections, status counts, confirmed and
probable IDs with evidence locations, unknown items with their required tests, excluded
corpora with reasons, and whether `ledger verify` passed. Candidate weaknesses stay
ledger entries; the main session drafts findings and runs them through the required
`findings-reviewer` workflow.

Under `automatic-analysis`, never pause to ask how to select or disposition an entry.
Include a plausibly applicable slice when evidence is ambiguous, process every batch, and
use `unknown` with an exact required test and blocker when the case evidence cannot
decide. Return those tests so the main session can run every safe, authorized one and
revisit the entry. Do not relax scope, isolation, evidence, or snapshot-drift
requirements.

"Complete" means `ledger verify` passed for the named snapshots and selections. It never
means all possible weaknesses for all time.
