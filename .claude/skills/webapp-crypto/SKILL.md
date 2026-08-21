---
name: webapp-crypto
description: Analyze client-side cryptography in live web applications, covering bundled JS crypto, WebCrypto usage, token and session handling, and browser-stored key material. Use whenever examining a web application's use of encryption, signing, or tokens; when reverse engineering obfuscated or minified JavaScript that touches crypto; or when assessing whether a browser-based protection scheme actually protects anything.
---

# Web application cryptography

Everything here touches a live target. Read `cases/<case>/SCOPE.md` and confirm the origin
is in scope before the first request. Analyzing a downloaded bundle on disk is local work
and needs no gate; loading the app does.

## The framing question

Client-side cryptography in a browser is executed by code the server sent, on data the
user already has. Before analyzing the mechanism, establish what it is supposed to achieve
and against whom. A large share of findings in this area are that the scheme protects
against nothing, because the attacker controls the execution environment. Say that plainly
in the finding rather than only cataloguing implementation flaws.

Client-side crypto is legitimate and worth deep analysis in these cases: end-to-end
encrypted messaging, zero-knowledge password proofs, client-held key material where the
server is explicitly untrusted, and signing where the private key never leaves the device.
Judge the implementation against that intent.

## Locating the crypto

Start with the bundle on disk. Pull the JS, then search it locally rather than grepping
through a live page:

```bash
# after saving bundles to cases/<case>/artifacts/
grep -oE 'crypto\.subtle\.[a-zA-Z]+' bundle.js | sort | uniq -c
grep -inE 'CryptoJS|forge|sjcl|libsodium|tweetnacl|jsencrypt|elliptic|jose' bundle.js
grep -inE 'encrypt|decrypt|sign|verify|deriveKey|importKey|generateKey' bundle.js
```

Source maps collapse this work entirely, so check for `.map` files and
`//# sourceMappingURL` before attempting to read minified output.

For WebCrypto specifically, the algorithm parameters passed to `importKey`, `deriveKey`,
and `encrypt` are the finding: they state the primitive, the mode, and the KDF iteration
count in plain text.

## Live inspection

Use a browser automation session (Playwright or CDP) on the main thread. It holds live
state and cannot be delegated. What to collect:

- Network layer: request and response bodies, to correlate client-side ciphertext with
  what actually crosses the wire.
- Storage: `localStorage`, `sessionStorage`, IndexedDB, and cookies. Keys and tokens in
  `localStorage` are readable by any script on the origin, which makes XSS a
  key-compromise vector rather than a session-hijack one.
- Runtime hooking: wrapping `crypto.subtle` methods to log arguments is usually faster
  than reading obfuscated code.

```javascript
// inject before app code runs
for (const m of ['encrypt','decrypt','sign','importKey','deriveKey']) {
  const orig = crypto.subtle[m].bind(crypto.subtle);
  crypto.subtle[m] = (...args) => { console.log(m, args); return orig(...args); };
}
```

- Key extractability: a `CryptoKey` created with `extractable: true` can be exported by
  any script on the page. Non-extractable keys are meaningfully stronger, and the
  difference belongs in the finding.

## Tokens and session material

Decode rather than assume. For JWTs, the header and payload are base64url and readable
without any secret. What matters is the `alg` value, whether the signature is verified
server-side, and whether `alg: none` or an HMAC/RSA confusion is accepted. Test these
against the server only if `SCOPE.md` authorizes active testing; otherwise record the
client-side observation and flag it for verification.

Session tokens that decode to structured data, contain a predictable counter, or carry a
recognizable timestamp are worth entropy analysis. Genuinely random tokens are not.

## Applying the checklist

Walk `crypto-primitive-id`'s `references/weakness-checklist.md` against what you find. The
items that recur most in browser code: keys derived from passwords with a low PBKDF2
iteration count, `Math.random()` used for anything security-relevant, AES-CBC with no MAC,
static IVs embedded in the bundle, and secrets shipped in the JS itself.
