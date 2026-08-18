---
name: artifact-intake
description: Safely import a binary, packet capture, certificate, archive, or other supplied artifact into an existing case, preserving provenance and computing identity before analysis. Use when a user provides a new local artifact, asks to add a sample to a case, or when a file outside cases/ is about to be analyzed.
---

# Artifact intake

This skill imports a local artifact; it does not fetch one. The destination case must
already exist. If it does not, use `new-case` first. Static intake does not require a
completed live-target scope, but never infer authorization to contact anything named
inside the artifact.

## Procedure

1. Resolve the source to a regular file. Reject symlinks, directories, device files,
   sockets, and paths inside `.git/` or secret stores.
2. Read the case's `SCOPE.md` and `NOTES.md`. Confirm the artifact belongs to that
   case; if the mapping is ambiguous, ask before copying.
3. Compute SHA-256 at the source using the installed hash tool:

   ```bash
   sha256sum SOURCE
   # macOS fallback
   shasum -a 256 SOURCE
   ```

4. Copy, never move, into `cases/<case>/artifacts/`. Preserve the original basename.
   If that name exists, compare hashes. Do not overwrite: identical means intake is
   already complete; different means stop and ask for a distinct filename.
5. Hash the destination and require an exact match with the source.
6. Append a provenance object to the case's `ARTIFACTS.json` (a JSON array). Read the
   file, append, and write it back as valid JSON — one object per artifact:

   ```json
   { "path": "artifacts/<file>", "sha256": "<hash>", "size": <bytes>,
     "file_type": "<file output>", "source": "<who supplied it, when — avoid leaking
     sensitive absolute paths into versioned notes>" }
   ```

   Then add a one-line dated pointer to `NOTES.md` ("intook artifacts/<file> — see
   ARTIFACTS.json"), not the full hash block.
7. Make derived files only under `extracted/`; the copy in `artifacts/` is immutable.

Do not unpack, execute, upload, or contact indicators found in the artifact during
intake. Those are separate analysis actions with their own authorization boundaries.
