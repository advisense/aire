# Scope: demo

**Status:** AUTHORIZED (self-authorized demo, black-box only).
**Date:** 2026-08-21
**Analyst:**

## Target

`http://127.0.0.1:8000` — a locally-hosted web application, treated as a black box (no
source code provided). Application identity/version not yet established; to be
determined during recon.

## Authorization

Self-authorized by the analyst (Carsten Maartmann-Moe) for demo / workflow-testing
purposes, 2026-08-21. No external client, engagement letter, or SOW. Since the target
is a local loopback service under the analyst's own control, no third party is
impacted.

## In scope

- `http://127.0.0.1:8000` — entire application surface reachable at this origin
  (all paths, ports as exposed at this address).

## Out of scope

- Anything not served from `http://127.0.0.1:8000` (no other hosts, ports, or
  third-party services).
- White-box artifacts: source code, config, or credentials not discoverable via
  black-box interaction with the running application.

## Permitted activity

Check what applies:

- [x] Static analysis of provided artifacts
- [x] Passive traffic capture on our own connections
- [x] Interactive analysis of the live application
- [x] Active testing that sends crafted input to the target
- [x] Creation and execution of PoCs that shows impact or confirms existence
- [ ] Testing against production
- [ ] Testing outside agreed hours

Black-box only: no source review, no credentials or internal access beyond what the
application itself exposes.

## Constraints

No rate limits or time windows specified (local demo target). No notification contacts
required — self-authorized. Nothing found is expected to contain real personal data;
treat any unexpected PII as sensitive and stop to flag it.

## Handling

No externally supplied artifacts yet. Anything downloaded or extracted during analysis
goes under `cases/demo/artifacts/` or `cases/demo/extracted/` per the case-workflow
skill, with provenance recorded in `ARTIFACTS.json`.
