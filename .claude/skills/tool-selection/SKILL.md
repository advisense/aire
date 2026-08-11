---
name: tool-selection
description: Select available local reverse-engineering tools without assuming a Linux workstation. Use before the first analysis in a new environment, when a documented command is unavailable, when asked what tooling is installed, or before recommending an installation.
---

# Tool selection

Use the smallest installed command that answers the question. Never install software,
modify the host, or download a tool without asking the user first.

## Discover capabilities

Run the repository's read-only inventory:

```bash
./tools/tool-doctor.sh
```

Treat its output as capabilities, not a shopping list. Missing optional tools do not
block analysis when an installed fallback can answer the question.

## Portable command map

| Need | Preferred | Installed fallback |
|---|---|---|
| SHA-256 | `sha256sum FILE` | `shasum -a 256 FILE` |
| ELF metadata | `readelf -h -l -S FILE` | `objdump -f -h FILE` |
| Mach-O metadata | `otool -hv -l FILE` | `objdump -f -h FILE` |
| Dynamic libraries | `ldd FILE` | `otool -L FILE` |
| Symbols | `nm -D FILE` | `nm -gU FILE` on macOS |
| Hex view | `xxd FILE` | `hexdump -C FILE` |
| Object disassembly | `objdump -d FILE` | `otool -tvV FILE` for Mach-O |
| TLS/certificates | `openssl` | none; request installation if needed |
| Packet captures | `tshark`, `capinfos` | none; request Wireshark CLI tools |

First identify the file format with `file`; then choose format-specific commands. Do
not run every variant and do not treat an unsupported-format error as evidence about
the artifact.

## Optional specialist tools

Rizin/radare2, binwalk, YARA, Frida, and Ghidra are enhancements, not baseline
requirements. If one would materially shorten the work and no installed tool covers
the need, explain the exact capability it adds and ask the user to install it. Do not
quietly substitute a network service or upload an artifact.

## Live and executable tools

`openssl s_client`, live `tshark` capture, mitmproxy, and browser automation generate
traffic: read the case `SCOPE.md` first. Debuggers and instrumentation execute or
attach to code: use only inside the isolation model in `docs/architecture.md`.
