# Corpus schema

`registry.json` contains `schema_version` and a `corpora` array. Each corpus record has:

```json
{
  "name": "crypto-core",
  "version": "2026.08",
  "description": "Primitive-independent and general cryptographic weaknesses",
  "path": "crypto-core/entries.jsonl",
  "updated": "2026-08-12",
  "sources": [{"title": "Source title", "url": "https://example.test"}]
}
```

Names use lowercase letters, digits, and hyphens. Versions are immutable snapshot
labels. `path` is relative to this directory.

Each nonblank line of an entries file is one JSON object:

```json
{
  "id": "AEAD-001",
  "title": "Nonce reuse with GCM",
  "summary": "The same nonce is used more than once with one key.",
  "categories": ["aead", "nonce-management"],
  "tags": ["aes-gcm", "forgery"],
  "applicable_when": ["The target encrypts two or more messages with one GCM key."],
  "check": ["Trace nonce generation and persistence across restart and concurrency."],
  "evidence": ["Repeated key/nonce pairs or a code path that can generate them."],
  "impact": "Plaintext relationships leak and authentication forgery may become possible.",
  "remediation": "Guarantee nonce uniqueness for each key.",
  "false_positives": ["The apparent reuse occurs under different keys."],
  "references": [{"title": "Source title", "url": "https://example.test", "locator": "Section 1"}]
}
```

Required fields are `id`, `title`, `summary`, `categories`, `applicable_when`, `check`,
`evidence`, `impact`, `remediation`, and `references`. IDs use uppercase letters,
digits, and hyphens and are unique within a corpus. Entries are sorted by ID.
