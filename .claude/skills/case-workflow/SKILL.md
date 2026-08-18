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
  ARTIFACTS.json    Identity + provenance: path, sha256, size, file_type, source.
  EVIDENCE.jsonl    Reproducible observations (O-NNN). Managed with ./tools/evidence.
  HYPOTHESES.md     Interpretations, alternatives, falsification tests (H-NNN).
  FINDINGS.md       Reviewed conclusions that cite observation IDs. The deliverable.
  DRAFT-FINDINGS.md Findings awaiting findings-reviewer. Promote or discard after review.
  NOTES.md          Chronological log and dead ends. Never authoritative.
  CORPUS-COVERAGE.json  Generated, version-pinned weakness review ledger (when used).
  artifacts/        Original samples, immutable. Hash on intake, never edit.
  extracted/        Anything derived: unpacked binaries, decoded blobs, keys, certs.
  scripts/          Case-specific tooling — parsers, decryptors, harnesses.
  reports/          Rendered output for the client or the file.
```

Case memory is layered by trust. An **observation** in `EVIDENCE.jsonl` is a located,
reproducible fact ("AES S-box bytes occur at offset 0x4A2C10"). A **hypothesis** in
`HYPOTHESES.md` is what that might mean ("the program implements AES") — never true until
its falsification test is run. A **finding** in `FINDINGS.md` is a reviewed conclusion
that cites the observations backing it. `EVIDENCE.jsonl` is trusted over `NOTES.md`, but
any observation that becomes a finding's premise is re-run from the artifact first.

Create `CORPUS-COVERAGE.json` only through the `corpus-lookup` skill. It records which
registered corpus snapshots were reviewed and the disposition of each entry; do not
hand-edit it or treat it as a substitute for `FINDINGS.md`. (Its per-check `evidence`
justification field is internal to the ledger and unrelated to `EVIDENCE.jsonl`.)

## Intake

Copy the artifact in rather than working from wherever it landed, then record identity
in `ARTIFACTS.json` before anything else — one object per artifact:

```json
{ "path": "artifacts/fw.bin", "sha256": "…", "size": 482304,
  "file_type": "ELF 64-bit LSB executable", "source": "Provided by client on 2026-08-14" }
```

Use the `artifact-intake` skill: it does collision checks, verifies the source and
destination hashes match, and appends the provenance object to `ARTIFACTS.json`
(a one-line pointer goes in `NOTES.md`, not the hash block).

Never modify anything in `artifacts/`. Unpacking, patching, and decoding produce new
files in `extracted/`, so the chain from original to derived stays reconstructable.

## Recording observations

Every located, reproducible fact goes into `EVIDENCE.jsonl` as an observation, through
`./tools/evidence` — never hand-edit the file:

```bash
./tools/evidence add cases/<case> \
  --artifact artifacts/fw.bin --location "file offset 0x4A2C10" \
  --observed "Bytes match the standard AES forward S-box." \
  --reproduce "xxd -s 0x4A2C10 -l 256 artifacts/fw.bin" \
  --caveats "Presence does not establish reachability or use."
```

A good observation is **atomic** (one claim), **located** (file/offset/packet/line),
**reproducible** (the smallest command that regenerates it), **interpretation-free**
(what was seen, not what it means), and **caveated** (what it does *not* prove). Mark it
`verified` only after re-running its `reproduce` command:
`./tools/evidence verify cases/<case> O-017`.

Observations are **superseded, never edited**. A correction is a new observation:
`./tools/evidence supersede cases/<case> O-009 …` stamps the old one and links the two,
so the case can self-correct without erasing how the mistake arose. Record a genuine
conflict with `contradict … --by O-009 --resolution "O-009 read the virtual address as a
file offset"`.

## Recording hypotheses

An interpretation of the observations is a hypothesis, not a finding. Record it in
`HYPOTHESES.md` with the observations that support it, the competing explanations, and
the smallest test that would falsify it:

```markdown
## H-04 — fw.bin implements AES encryption
**Interpretation:** The AES tables at O-017 are used by reachable code.
**Supported by:** O-017, O-031
**Alternatives:** Dead constant table linked but never called; AES used only for
                  firmware-signature checking, not data encryption.
**Falsification test:** Cross-reference 0x4A2C10; if no reachable call site loads it,
                        the claim fails.
**Status:** open
```

Promote a hypothesis to a finding only after its falsification test has been run and it
survives.

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
**Evidence:** O-017 (AES S-box bytes @ 0x4A2C10), O-023 (16-byte IV literal loaded
from .rodata:0x4A31A0 into the IV parameter on every call — no per-message IV). Both
verified.
**Impact:** Identical plaintexts produce identical ciphertexts across messages,
leaking equality and enabling chosen-plaintext distinguishing.
**Remediation:** Generate a random IV per message and transmit it with the record.
```

The `**Evidence:**` field cites observation IDs from `EVIDENCE.jsonl` with a one-line
gloss each — it does not restate raw reproduction. A finding may not cite an observation
that is not yet `verified`.

Confidence takes one of three values, and the distinction matters more than it looks:

- **Confirmed** — verified by execution, test vector match, or successful decryption.
- **Probable** — strong structural evidence, not yet executed against.
- **Hypothesis** — worth testing, not yet supported. These belong in `HYPOTHESES.md`
  until their falsification test promotes them, not in `FINDINGS.md`.

## Working log

`NOTES.md` is append-only, timestamped, and **never authoritative** — it is narrative,
not a source of facts. Reproducible facts live in `EVIDENCE.jsonl`, interpretations in
`HYPOTHESES.md`, provenance in `ARTIFACTS.json`. Use `NOTES.md` for what was tried, in
what order, and what dead-ended: "ruled out RC4: no 256-byte identity permutation in the
init path" is as valuable as a positive result. Before ending a session, append a short
"next steps" block so a cold start has somewhere to begin.

## Resuming a case

Read `SCOPE.md`, then `FINDINGS.md`, then the verified observations in `EVIDENCE.jsonl`
(`./tools/evidence list cases/<case>`), then the last ~50 lines of `NOTES.md`. That is
usually enough to resume without re-reading artifacts. Trust `EVIDENCE.jsonl` over
`NOTES.md`, and re-run any observation you are about to build a finding on.
