# Scope — <CASE NAME>

**Status:** DRAFT — no live target may be contacted until this file is complete.
**Date:** <YYYY-MM-DD>
**Analyst:**

## Target

What is being analyzed. Be specific: file names and hashes for artifacts, exact
hostnames and URLs for live systems, version numbers where known.

## Authorization

Who authorized this work, in what document, and on what date. Link or reference the
engagement letter, statement of work, or internal approval. If this section is empty,
the work is not authorized.

## In scope

Systems, hosts, domains, and artifacts that may be analyzed. Live hosts must be listed
explicitly — a domain being related to the client is not the same as being in scope.

## Out of scope

Systems explicitly excluded. Third-party services, production databases, anything
shared with other tenants, and anything not named in the section above.

## Permitted activity

Check what applies:

- [ ] Static analysis of provided artifacts
- [ ] Passive traffic capture on our own connections
- [ ] Interactive analysis of the live application (no state changes)
- [ ] Interactive analysis of the live application (state changes permitted)
- [ ] Active testing that sends crafted input to the target
- [ ] Verification of vulnerabilities (minimal PoCs only; no weaponized exploits)
- [ ] Testing against production
- [ ] Testing outside agreed hours

## Constraints

Rate limits, time windows, data handling requirements, notification contacts, and
anything that must be reported immediately rather than held for the report.

## Handling

Where the artifacts came from, how long they may be retained, and how they are to be
disposed of. Note anything containing personal data.
