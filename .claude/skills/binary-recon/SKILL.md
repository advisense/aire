---
name: binary-recon
description: Triage and analyze compiled binaries and firmware — identify format and architecture, spot packing, find and follow cryptographic routines, and set up dynamic analysis. Use whenever working with an executable, shared library, firmware image, or any unidentified binary blob, and whenever asked what a binary does, how it protects data, or where a particular routine lives.
---

# Binary reconnaissance

Work in `cases/<case>/`. Never execute a sample outside the sandbox described in
`docs/architecture.md`.

## Triage sequence

Run the cheap identification pass first. It costs seconds and often reframes the
whole engagement:

```bash
file <bin>
sha256sum <bin>                         # Linux
shasum -a 256 <bin>                     # macOS fallback
readelf -h -l -S <bin>                  # ELF
otool -hv -l <bin>                      # Mach-O
objdump -f -h <bin>                     # portable fallback
strings -a -n 6 <bin>
nm <bin>                                # symbols when present
```

Use `tool-selection` when a command is unavailable. Rizin/radare2 is optional; when
installed, `rabin2 -I`, `-z`, and `-i` provide a convenient format-neutral pass.

Delegate this to the `binary-triage` subagent when the binary is large or when you
want the raw output kept out of the main context.

**Entropy first.** A high-entropy section suggests packing, compression, or embedded
ciphertext, and changes what every subsequent step means:

```bash
binwalk -E <bin>      # entropy curve
binwalk -Y <bin>      # opcode/architecture detection
binwalk -e <bin>      # extract embedded filesystems and blobs — firmware especially
```

`binwalk` is optional. If it is absent, inspect section sizes and bytes with the
format-specific tools above and use a small case-local Python entropy script only
when entropy would change the next step. Ask before installing specialist tooling.

Flat entropy near 8.0 across the whole file means packed or encrypted; unpack before
analyzing. Localized high-entropy regions in an otherwise normal binary are usually
embedded keys, certificates, or compressed resources — extract them to `extracted/`.

## Finding the crypto

Combine three approaches; they fail in different ways:

1. **Imports and symbols** — see the `crypto-primitive-id` skill, step 1.
2. **Constant scanning** — `yara` with FindCrypt-style rules, or rizin's `/ca` and
   `/c` searches. Cross-reference every hit to a caller before believing it.
3. **Call-graph position** — cryptographic routines cluster near serialization,
   network I/O, and file writes. Working backwards from `send`, `write`, or a
   protocol parser often reaches the crypto faster than scanning for it.

Once located, the questions that produce findings are about the *call site*, not the
algorithm: where does the key come from, is the IV fresh, is the output
authenticated, what happens on error.

## Static analysis

For scripted extraction, drive rizin/radare2 in batch mode from Bash rather than
holding an interactive session:

```bash
rizin -qc 'aaa; afl' <bin>              # analyze, list functions
rizin -qc 'aaa; pdf @ sym.encrypt' <bin>  # disassemble one function
rizin -qc 'izz~key' <bin>                 # search all strings
```

Keep output narrow. `pdf` on one function is useful; `pd` across a whole binary
floods the context and should be delegated to a subagent that returns a summary.

Ghidra headless suits bulk decompilation to C-like output, which is often far more
readable than disassembly for understanding a crypto routine's logic. Write
decompiled functions of interest to `extracted/` so later sessions can read them
without re-running the decompiler.

## Dynamic analysis

Dynamic work holds live state, so keep it on the main thread — subagents cannot share
a debugger or instrumentation session.

- **Debugger** (gdb/pwndbg, lldb, x64dbg) — breakpoint on the identified crypto
  function and read the key and IV out of registers or memory at call time. This is
  usually the shortest path from "probably AES-CBC" to a confirmed key.
- **Instrumentation** (Frida) — hook library crypto functions to log every key, IV,
  plaintext, and ciphertext passing through. Effective against statically-linked and
  obfuscated code where static analysis stalls.
- **Emulation** (Qiling, Unicorn) — run an isolated routine against known input when
  the full binary will not execute in your environment. Good for firmware.

Record every recovered key or parameter in `extracted/` with a note in `NOTES.md`
saying where it came from, so the provenance survives the session.

## When static analysis stalls

Obfuscation, virtualization, and anti-debug are cost decisions, not walls. Before
committing to deobfuscation, ask whether a dynamic approach reaches the same answer
faster: the plaintext has to exist in memory at some point, and hooking is usually
cheaper than defeating a protector.
