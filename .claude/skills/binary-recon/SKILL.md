---
name: binary-recon
description: Triage and analyze compiled binaries and firmware. Identify format and architecture, spot packing, find and follow cryptographic routines, and set up dynamic analysis. Use whenever working with an executable, shared library, firmware image, or any unidentified binary blob, and whenever asked what a binary does, how it protects data, or where a particular routine lives.
---

# Binary reconnaissance

Work in `cases/<case>/`.

## Triage sequence

The cheap identification pass costs seconds and often reframes the engagement:

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

Use `tool-selection` when a command is unavailable. Rizin/radare2 is optional; when it is
installed, `rabin2 -I`, `-z`, and `-i` give a format-neutral pass. Delegate to the
`binary-triage` subagent when the binary is large or the raw output should stay out of
the main context.

Check entropy early, because it changes what every later step means:

```bash
binwalk -E <bin>      # entropy curve
binwalk -Y <bin>      # opcode/architecture detection
binwalk -e <bin>      # extract embedded filesystems and blobs, firmware especially
```

`binwalk` is optional. Without it, inspect section sizes and bytes with the
format-specific tools above, and write a small case-local Python entropy script only when
entropy would change the next step. Ask before installing specialist tooling.

Flat entropy near 8.0 across the whole file means packed or encrypted, so unpack before
analyzing. Localized high-entropy regions in an otherwise normal binary are usually
embedded keys, certificates, or compressed resources; extract them to `extracted/`.

## Finding the crypto

Combine three approaches; they fail in different ways:

1. Imports and symbols. See `crypto-primitive-id`, step 1.
2. Constant scanning: `yara` with FindCrypt-style rules, or rizin's `/ca` and `/c`.
   Cross-reference every hit to a caller before believing it.
3. Call-graph position. Crypto clusters near serialization, network I/O, and file writes.
   Working backwards from `send`, `write`, or a protocol parser often beats scanning.

Once the routine is located, the findings come from the call site rather than the
algorithm: where the key comes from, whether the IV is fresh, whether the output is
authenticated, and what happens on error.

## Static analysis

Drive rizin/radare2 in batch mode from Bash rather than holding an interactive session:

```bash
rizin -qc 'aaa; afl' <bin>                # analyze, list functions
rizin -qc 'aaa; pdf @ sym.encrypt' <bin>  # disassemble one function
rizin -qc 'izz~key' <bin>                 # search all strings
```

Keep output narrow. `pdf` on one function is useful; `pd` across a whole binary floods
the context, so delegate that to a subagent that returns a summary.

Ghidra headless suits bulk decompilation to C-like output, which is often far more
readable than disassembly for a crypto routine's logic. Write decompiled functions of
interest to `extracted/` so later sessions can skip the decompiler.

## Dynamic analysis

Dynamic work holds live state, so keep it on the main thread. Subagents cannot share a
debugger or instrumentation session.

- Debugger (gdb/pwndbg, lldb, x64dbg): breakpoint the identified crypto function and read
  the key and IV from registers or memory at call time. Usually the shortest path from
  "probably AES-CBC" to a confirmed key.
- Instrumentation (Frida): hook library crypto to log every key, IV, plaintext, and
  ciphertext. Effective against statically-linked and obfuscated code where static
  analysis stalls.
- Emulation (Qiling, Unicorn): run an isolated routine against known input when the full
  binary will not execute in your environment. Good for firmware.

Record every recovered key or parameter in `extracted/`, with a `NOTES.md` line saying
where it came from, so the provenance survives the session.

## When static analysis stalls

Obfuscation, virtualization, and anti-debug are cost decisions, not walls. Before
committing to deobfuscation, ask whether a dynamic approach reaches the same answer
faster: the plaintext has to exist in memory at some point, and hooking is usually
cheaper than defeating a protector.
