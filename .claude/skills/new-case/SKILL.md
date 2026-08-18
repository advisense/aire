---
name: new-case
description: Scaffold a new case directory for a reverse engineering target. Run with /new-case <case-name>.
argument-hint: "case-name"
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit
---

Create a new case directory for the target named in $ARGUMENTS.

1. Validate the name: lowercase, hyphens, no spaces or path separators. If
   `cases/$ARGUMENTS` already exists, stop and report it rather than overwriting.
2. Copy `cases/TEMPLATE/` to `cases/$ARGUMENTS/` and create the `artifacts/`,
   `extracted/`, `scripts/`, and `reports/` subdirectories. The copy includes
   `ARTIFACTS.json` (initialized to `[]`) and an empty `EVIDENCE.jsonl`; leave both as
   copied — `artifact-intake` and `./tools/evidence` populate them.
3. Fill the case name and today's date into the copied `SCOPE.md`, `FINDINGS.md`,
   `NOTES.md`, and `HYPOTHESES.md` headers.
4. Ask the user for the scope essentials and write them into `SCOPE.md`: what the
   target is, who authorized the work, what is explicitly in and out of bounds, and
   any live hosts or domains that may be contacted. Do not invent these.
5. Report the created path and remind the user that nothing live should be touched
   until `SCOPE.md` is filled in.
