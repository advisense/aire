---
name: case-workflow
description: The case directory contract for reverse engineering work — where artifacts, findings, and notes live, how to intake a sample, and the required format for recording a finding. Use this whenever starting work on a target, resuming a case after a break, recording a finding, or writing up results. Also use when a task mentions a case name, an artifact path under cases/, or asks "where were we" on a target.
---

# Case workflow

A case is one target: one binary, one application, one capture campaign. Everything
about that target lives in `cases/<case-name>/`. This directory is the project's
durable memory — it survives context compaction, session restarts, and handoffs
between the main thread and subagents.

## Directory contract

```
cases/<case-name>/
  SCOPE.md          Authorization boundary. Read before touching anything live.
  FINDINGS.md       Confirmed conclusions with evidence. The deliverable.
  DRAFT-FINDINGS.md Findings awaiting findings-reviewer. Promote or discard after review.
  NOTES.md          Working log: hypotheses, dead ends, what to try next.
  CORPUS-COVERAGE.json  Generated, version-pinned weakness review ledger (when used).
  artifacts/        Original samples, immutable. Hash on intake, never edit.
  extracted/        Anything derived: unpacked binaries, decoded blobs, keys, certs.
  scripts/          Case-specific tooling — parsers, decryptors, harnesses.
  reports/          Rendered output for the client or the file.
```

Create `CORPUS-COVERAGE.json` only through the `corpus-lookup` skill. It records which
registered corpus snapshots were reviewed and the evidence-backed disposition of each
entry; do not hand-edit it or treat it as a substitute for `FINDINGS.md`.

## Intake

Copy the artifact in rather than working from wherever it landed, then record identity
before anything else:

```bash
cp <source> cases/<case>/artifacts/
cd cases/<case>/artifacts && sha256sum <file> | tee -a ../NOTES.md
# macOS fallback: shasum -a 256 <file> | tee -a ../NOTES.md
file <file> && ls -l <file>
```

Use the `artifact-intake` skill for collision checks, source/destination hash
verification, and the complete provenance record.

Never modify anything in `artifacts/`. Unpacking, patching, and decoding produce new
files in `extracted/`, so the chain from original to derived stays reconstructable.

## Recording findings

Draft findings go into `DRAFT-FINDINGS.md` first. Delegate the draft to
`findings-reviewer`, reconcile the verdict, then move the accepted finding to
`FINDINGS.md` and delete it from the draft file. Never write directly to
`FINDINGS.md` — the review gate is mandatory.

`FINDINGS.md` holds only conclusions you would defend in a report. Use this structure:

```markdown
## F-01 — AES-128-CBC with a hardcoded IV

**Confidence:** Confirmed
**Location:** artifacts/fw.bin @ 0x4A2C10 (key schedule), 0x4A31A0 (IV)
**Evidence:** AES T-table constants at 0x4A2C10 matched via yara rule
crypto/aes_te.yar. Cross-reference at 0x4A2E80 loads a 16-byte literal from
.rodata:0x4A31A0 into the IV parameter on every call — no per-message IV.
**Impact:** Identical plaintexts produce identical ciphertexts across messages,
leaking equality and enabling chosen-plaintext distinguishing.
**Remediation:** Generate a random IV per message and transmit it with the record.
```

Confidence takes one of three values, and the distinction matters more than it looks:

- **Confirmed** — verified by execution, test vector match, or successful decryption.
- **Probable** — strong structural evidence, not yet executed against.
- **Hypothesis** — worth testing, not yet supported. These belong in NOTES.md until
  they earn promotion.

## Working log

`NOTES.md` is append-only and timestamped. Record dead ends explicitly — "ruled out
RC4: no 256-byte identity permutation in the init path" is as valuable as a positive
result, because it stops the next session from re-deriving it. Before ending a session,
append a short "next steps" block so a cold start has somewhere to begin.

## Resuming a case

Read `SCOPE.md`, then `FINDINGS.md`, then the last ~50 lines of `NOTES.md`. That is
usually enough to resume without re-reading artifacts. Do not re-run triage that
NOTES.md already records.
