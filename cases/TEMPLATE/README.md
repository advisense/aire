# Case template

`/new-case <name>` copies this directory to `cases/<name>/` and creates:

```
artifacts/    Original samples. Immutable — hash on intake, never edit.
extracted/    Derived material: unpacked binaries, decoded blobs, keys, triage output.
scripts/      Case-specific parsers, decryptors, and harnesses.
reports/      Rendered deliverables.
```

Case memory is layered by how much it can be trusted:

```
ARTIFACTS.json   Identity + provenance (path, sha256, size, file_type, source).
EVIDENCE.jsonl   Reproducible observations (O-NNN). Managed with ./tools/evidence.
HYPOTHESES.md    Interpretations, alternatives, falsification tests (H-NNN).
NOTES.md         Chronological log and dead ends. Never authoritative.
DRAFT-FINDINGS.md  Conclusions awaiting findings-reviewer.
FINDINGS.md      Reviewed conclusions — the deliverable. Findings cite O-NNN.
```

`EVIDENCE.jsonl` is trusted over `NOTES.md`: an observation is a located, reproducible
fact; a note is narrative. Any observation that becomes a finding's premise is
re-run from the artifact before it is relied on.

Fill in `SCOPE.md` before touching any live target.

When performing a corpus-backed weakness review, the `corpus-lookup` skill generates
`CORPUS-COVERAGE.json` in the case directory. It is intentionally absent from a new
case until corpus selections have been made.

Once `SCOPE.md` is complete, `/automatic-analysis cases/<case-name>` performs an
unattended corpus-backed review. It asks no questions: tests outside the recorded
scope or unavailable in the current environment are preserved as `unknown` with an
exact blocker instead of being silently skipped.
