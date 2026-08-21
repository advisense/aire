# Cryptographic weakness checklist

Walk this after identifying primitives. Nearly all real findings are composition
failures, not broken primitives. Each item states what to look for and why it matters, so
the finding can be recorded with impact per the `case-workflow` format.

This is the fast first-pass checklist, not an exhaustive catalog. For auditable coverage,
use the `corpus-lookup` skill to select versioned corpora and maintain the case's
`CORPUS-COVERAGE.json` ledger without loading the corpus wholesale.

## Key material

- **Hardcoded keys in the binary or client bundle.** A key shipped to the user is not a
  secret. Check `.rodata`, resource sections, and JS bundles for 16/24/32-byte literals
  feeding key parameters.
- **Key derived from a low-entropy input** (device ID, username, timestamp, short PIN)
  without a slow KDF. The search space, not the cipher, becomes the security boundary.
- **Password used directly as a key**, or hashed once with a fast hash. Look for the
  absence of PBKDF2/scrypt/Argon2/bcrypt, or a PBKDF2 iteration count that is implausibly
  low.
- **Same key across all installations or all users.** One recovered key compromises the
  fleet.

## Randomness

- **`rand()`, `srand(time(NULL))`, `Math.random()`, Mersenne Twister, or an LCG** used to
  generate keys, IVs, nonces, session tokens, or password-reset material. These are
  predictable; MT19937 state is recoverable from 624 consecutive outputs.
- **Seeded from a predictable value** such as PID, boot time, or MAC address.
- **Correct API, wrong usage**: a CSPRNG called once and its output reused.

## Modes and IVs

- **ECB mode.** Identical plaintext blocks produce identical ciphertext blocks, leaking
  structure. Frequently visible as repeating 16-byte runs in ciphertext.
- **Static or hardcoded IV** with CBC. Defeats semantic security across messages.
- **Nonce reuse with a stream cipher, CTR mode, or GCM.** Catastrophic: for GCM it leaks
  the authentication subkey and allows forgery, not only plaintext recovery.
- **Predictable or counter-based IV** with CBC where an attacker can influence plaintext.

## Integrity and authentication

- **Encryption without authentication.** CBC or CTR with no MAC leaves ciphertext
  malleable. Look for the absence of any tag alongside the ciphertext.
- **MAC-then-encrypt or encrypt-and-MAC** rather than encrypt-then-MAC.
- **CRC or a plain hash used where a MAC is required.** An unkeyed checksum is forgeable
  by anyone who can modify the message.
- **Non-constant-time comparison of MACs, tags, or tokens**: `memcmp`, `strcmp`, or `==`
  on secrets. Distinguishable by timing.

## Transport and trust

- **Certificate or hostname validation disabled**: `verify=False`, a permissive
  `TrustManager`, `SSL_VERIFY_NONE`, or a callback that returns success unconditionally.
- **Cryptography implemented over HTTP** to compensate for the absence of TLS. Usually
  indicates the threat model was never written down.
- **Downgrade paths**: a fallback branch that proceeds unencrypted on error.

## Asymmetric specifics

- **Textbook RSA**: no OAEP for encryption, no PSS or PKCS#1 v1.5 for signatures.
- **Signature verification that checks the wrong thing**, or where an error path is
  treated as success.
- **Small or non-standard public exponent**, unvalidated curve points, or missing cofactor
  handling.

## Deprecated primitives

MD5 and SHA-1 for signatures or integrity; DES, 3DES, and RC4; RSA below 2048 bits; custom
ciphers of any kind. MD5 and SHA-1 remain acceptable for non-security uses such as content
addressing, so record the context, not only the algorithm name.
