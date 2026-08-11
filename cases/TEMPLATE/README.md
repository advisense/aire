# Case template

`/new-case <name>` copies this directory to `cases/<name>/` and creates:

```
artifacts/    Original samples. Immutable — hash on intake, never edit.
extracted/    Derived material: unpacked binaries, decoded blobs, keys, triage output.
scripts/      Case-specific parsers, decryptors, and harnesses.
reports/      Rendered deliverables.
```

Fill in `SCOPE.md` before touching any live target.
