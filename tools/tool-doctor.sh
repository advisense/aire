#!/bin/sh

# Report the local analysis capabilities this harness knows how to use. This script
# only inspects PATH; it does not install software or contact the network.

set -u

missing_required=0

first_available() {
  capability=$1
  requirement=$2
  shift 2

  for candidate in "$@"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      location=$(command -v "$candidate")
      printf '%-12s %-9s %-18s %s\n' "$capability" present "$candidate" "$location"
      return 0
    fi
  done

  printf '%-12s %-9s %-18s %s\n' "$capability" missing "-" "$requirement"
  return 1
}

printf '%-12s %-9s %-18s %s\n' CAPABILITY STATUS COMMAND DETAIL

first_available metadata required file || missing_required=1
first_available hashing required sha256sum shasum || missing_required=1
first_available hex required xxd hexdump || missing_required=1
first_available scripting required python3 || missing_required=1

first_available symbols optional nm || true
first_available objects optional readelf otool objdump || true
first_available crypto optional openssl || true
first_available packets optional tshark || true
first_available pcap-info optional capinfos || true
first_available proxy optional mitmproxy mitmdump || true
first_available isolation optional docker podman || true
first_available re-suite optional rizin r2 rabin2 || true
first_available firmware optional binwalk || true
first_available signatures optional yara || true
first_available instrument optional frida || true
first_available decompiler optional analyzeHeadless ghidraRun || true
first_available debugger optional lldb gdb || true

if [ "$missing_required" -ne 0 ]; then
  printf '\nOne or more baseline capabilities are missing.\n' >&2
  exit 1
fi
