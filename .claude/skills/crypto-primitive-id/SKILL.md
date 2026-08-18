---
name: crypto-primitive-id
description: Identify which cryptographic primitives a binary, protocol, or application uses — from magic constants, structural fingerprints, key and block sizes, and observable behaviour — and assess whether they are used correctly. Use this whenever analyzing anything that appears to encrypt, hash, sign, derive keys, or randomize; when you find high-entropy blobs, suspicious constant tables, or unexplained fixed-size fields; and whenever asked what algorithm something uses or whether the crypto is sound.
---

# Identifying cryptographic primitives

Identification proceeds from cheapest signal to most expensive. Most primitives are
identified in the first two steps; do not open a disassembler before exhausting them.

## 1. Named symbols and library evidence

The cheapest answer is that nobody rolled anything. Check imports, dynamic symbols,
and strings for `libcrypto`, `libsodium`, `mbedtls`, `wolfssl`, `bcrypt.dll`,
`CommonCrypto`, `Security.framework`, and the like.

```bash
nm -D <bin> 2>/dev/null | grep -iE 'aes|sha|rsa|ec|hmac|chacha|poly|md5|rc4|kdf'
strings -n 6 <bin> | grep -iE 'openssl|mbedtls|sodium|bearssl|wolfssl|nettle|gcrypt'
```

A named library import usually resolves the algorithm question and moves the
interesting work to *how* it is being called — mode, key handling, IV discipline —
which is where the real findings are.

## 2. Constant tables

Hand-rolled and statically-linked implementations betray themselves through
initialization constants and lookup tables. `references/constants.md` holds the
identification table: read it when scanning for constants.

Automate the scan where possible — `yara` with FindCrypt-style rules, `rizin`'s
`/ca` search, or `binwalk -Y`. A hit tells you the primitive is *present*; it does
not tell you it is *used*. Record the presence as an observation (`./tools/evidence
add`, with the offset and the `reproduce` command), and keep "the primitive is used" as
a `HYPOTHESES.md` entry until you have followed cross-references from the table to a
caller.

## 3. Structural fingerprints

When constants are absent — because the implementation is obfuscated, or the primitive
has none — fall back to shape:

| Observation | Suggests |
|---|---|
| 16-byte block boundaries, ciphertext length a multiple of 16 | AES or another 128-bit block cipher |
| 8-byte block boundaries | DES/3DES, Blowfish, or another 64-bit block cipher |
| Ciphertext length == plaintext length, no padding | Stream cipher or a block cipher in CTR/CFB/OFB |
| Fixed 32-byte output, no key input | SHA-256 or another 256-bit hash |
| Fixed 32-byte output, keyed | HMAC-SHA-256, or a MAC like Poly1305 |
| 12-byte nonce + 16-byte trailer | AEAD — AES-GCM or ChaCha20-Poly1305 |
| Big-integer arithmetic, modular exponentiation, 128/256/512-byte operands | RSA or finite-field Diffie-Hellman |
| 32-byte public values, no obvious padding | X25519 or Ed25519 |
| 64/65-byte values starting with 0x04 | Uncompressed NIST-curve EC point |
| DER structure (`30 82 ...`) | ASN.1-wrapped key, cert, or signature |

## 4. Behavioural confirmation

Structural evidence gives you Probable. To reach Confirmed, execute against known
answers: feed a test vector and check the output, or take a suspected key and IV and
attempt to decrypt a captured record. A successful decryption that produces
well-formed plaintext is the strongest evidence available, and it is worth the effort
of building a small harness in `cases/<case>/scripts/` to get there.

## 5. Assessing correctness

Identification is rarely the deliverable on its own. Once you know what is in use,
walk `references/weakness-checklist.md` — the recurring failures are in how primitives
are composed, not in the primitives themselves. Capture each supporting fact as an
observation in `EVIDENCE.jsonl` (`./tools/evidence add`), then draft the candidate
weakness in `DRAFT-FINDINGS.md` citing those `O-NNN` IDs and follow the `case-workflow`
skill: send it to `findings-reviewer`, reconcile the verdict, and move only accepted
findings to `FINDINGS.md`.
