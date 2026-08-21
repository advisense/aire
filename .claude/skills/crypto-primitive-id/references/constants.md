# Cryptographic constant reference

Identification table for constants that appear in statically-linked or hand-rolled
implementations. A match means the primitive is *present in the image*. Confirm by
cross-reference to a caller before recording it.

Byte order matters: most of these appear little-endian on x86 and ARM. Search both.

## Hashes

| Primitive | Signature |
|---|---|
| MD5 | 64-entry K table beginning `d76aa478 e8c7b756 242070db c1bdceee`; init `67452301 efcdab89 98badcfe 10325476` |
| SHA-1 | Round constants `5a827999 6ed9eba1 8f1bbcdc ca62c1d6`; same init as MD5 plus `c3d2e1f0` |
| SHA-256 | Init `6a09e667 bb67ae85 3c6ef372 a54ff53a`; 64-entry K table beginning `428a2f98 71374491 b5c0fbcf e9b5dba5` |
| SHA-512 | 64-bit init beginning `6a09e667f3bcc908 bb67ae8584caa73b`; 80-entry K table |
| SHA-3 / Keccak | 24-entry round constants beginning `0000000000000001 0000000000008082`; 1600-bit state |
| BLAKE2 | Reuses SHA-512 IV; distinguished by 10-row sigma permutation table |

SHA-256's IV is the fractional part of the square roots of the first 8 primes, and
SHA-512's the cube roots of the same primes. The values also appear in BLAKE2 and
elsewhere, so an IV match alone does not pin the algorithm.

## Block ciphers

| Primitive | Signature |
|---|---|
| AES | 256-byte S-box beginning `63 7c 77 7b f2 6b 6f c5 30 01 67 2b`; inverse S-box beginning `52 09 6a d5`; Rcon `01 02 04 08 10 20 40 80 1b 36`; T-tables are 1KB each and begin `c66363a5 f87c7c84` |
| DES | PC1/PC2 permutation tables, 8 S-boxes of 64 entries each |
| Blowfish | 4KB+ of pi-derived P-array and S-boxes beginning `243f6a88 85a308d3 13198a2e 03707344` |
| Camellia | Sigma constants `a09e667f3bcc908b b67ae8584caa73b2` |
| TEA/XTEA | Delta `9e3779b9`, the golden-ratio constant. It also appears in unrelated hash mixers, so confirm by loop shape |

## Stream ciphers and AEAD

| Primitive | Signature |
|---|---|
| ChaCha20 / Salsa20 | Constant string `expand 32-byte k` (or `expand 16-byte k` for 128-bit keys) |
| RC4 | No constants. Identify by KSA shape: a 256-byte array initialized to the identity permutation, then swapped in a 256-iteration loop |
| Poly1305 | Clamping mask `0ffffffc0ffffffc0ffffffc0fffffff` applied to the key |
| AES-GCM | AES core plus GF(2^128) multiplication; reduction polynomial `e1000000...` |

## Public key

| Primitive | Signature |
|---|---|
| Curve25519 / X25519 | Prime 2^255-19 as `ffffffffffffffff...ffffffed`; A24 constant `0x01db41` (121665) |
| Ed25519 | Curve25519 field plus base point and the constant `d = 0x52036cee...` |
| NIST P-256 | Prime `ffffffff00000001000000000000000000000000ffffffffffffffffffffffff` |
| secp256k1 | Prime `fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f` |
| RSA | No fixed constants. Identify by modexp loop, Montgomery reduction, and small public exponents (`010001` = 65537) |

## Encodings and containers

Frequently mistaken for cryptography; rule these out early.

| Marker | Meaning |
|---|---|
| `30 82` at offset 0 | DER SEQUENCE: cert, key, or signature |
| `-----BEGIN` | PEM |
| `1f 8b` | gzip (high entropy, not encrypted) |
| `78 9c` / `78 01` / `78 da` | zlib |
| `04 22 4d 18` | LZ4 |
| `fd 37 7a 58 5a` | XZ |
| CRC32 table beginning `00000000 77073096 ee0e612c` | Checksum, not a hash |

A CRC table in a "crypto" routine is a common false positive and an equally common real
finding: integrity checks built on CRC provide no authentication.
