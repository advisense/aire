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

Use `./tools/corpus-lookup`; never read corpus JSONL files directly. The command caps
and paginates output so only the current batch enters context. Do not contact live
targets, execute untrusted artifacts, modify `FINDINGS.md`, or hand-edit a coverage
ledger.

## Direct lookup

For a lookup question, use the smallest operation that answers it:

```bash
./tools/corpus-lookup corpora
./tools/corpus-lookup categories --corpus crypto-core
./tools/corpus-lookup search "GCM nonce reuse" --limit 10
./tools/corpus-lookup list --corpus crypto-core --category aead --limit 20
./tools/corpus-lookup show crypto-core:SYM-006
```

Follow the `next:` cursor from `list`; do not increase limits to load a corpus. Return
only the relevant entries and never claim exhaustive coverage from a search.

## Case audit

For an exhaustive case review:

1. Read `SCOPE.md`, `FINDINGS.md`, and recent `NOTES.md`.
2. Inspect `corpora` and `categories`. Include every corpus slice applicable to the
   target's primitives, protocols, platforms, and threat model; explicitly justify
   whole-corpus exclusions.
3. Preview selections before creating a ledger. A selection is a corpus, one category,
   or a category intersection using `+`:

   ```bash
   ./tools/corpus-lookup preview \
     --select crypto-core:aead --select crypto-core:rsa+side-channel
   ```

4. If no ledger exists, initialize it with the previewed selections:

   ```bash
   ./tools/corpus-lookup ledger init cases/<case> \
     --select crypto-core --select tls-pki:certificate-validation
   ```

   If one exists, continue its pinned selections. Never replace or widen it silently;
   stop and report version drift.
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

Do not use `ruled-out` merely because evidence was not found. If resolution requires
live traffic or executing an untrusted artifact, use `unknown` and name the exact test
the main session must perform.

Return a compact summary with pinned versions and selections, status counts,
confirmed/probable IDs and evidence locations, unknown items and required tests,
excluded corpora and reasons, and whether `ledger verify` passed. Candidate weaknesses
remain ledger entries; the main session drafts findings and sends them through the
required `findings-reviewer` workflow.

“Complete” means `ledger verify` passed for the named snapshots and selections. It
never means all possible weaknesses for all time.
