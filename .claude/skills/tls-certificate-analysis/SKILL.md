---
name: tls-certificate-analysis
description: Inspect local X.509 certificates, keys, PKCS containers, and TLS handshake evidence using OpenSSL and tshark. Use when given PEM, DER, PKCS#7, PKCS#12, certificate chains, or captured TLS handshakes, or when asked about certificate validity, identity, algorithms, or chain structure.
---

# TLS and certificate analysis

Prefer local artifacts and captured handshakes. `openssl s_client` contacts a live host,
so it requires an explicit in-scope hostname in `cases/<case>/SCOPE.md` first. Never print
private key material into the conversation or a report.

## Identify the container

Start with `file` and the first line or ASN.1 structure. Do not rely on the extension.

```bash
openssl x509 -in cert.pem -noout -subject -issuer -serial -dates -fingerprint -sha256
openssl x509 -inform DER -in cert.der -noout -subject -issuer -serial -dates
openssl asn1parse -in object.pem -i
openssl pkcs7 -in chain.p7b -print_certs -noout
```

For PKCS#12, list metadata without exporting keys. Supply passwords through an interactive
prompt or an approved secret mechanism, never a command-line argument or a checked-in
file.

## Evidence to collect

- Subject and SAN identities. SAN controls hostname matching, not the common name.
- Issuer and chain order, including missing intermediates.
- Not-before and not-after timestamps, evaluated against the relevant observation date
  rather than assumed current time.
- Public-key algorithm and size, signature algorithm, serial number, key usage, extended
  key usage, basic constraints, and SHA-256 fingerprint.
- For captured TLS: negotiated version and suite, SNI, ALPN, certificate chain, and
  whether resumption occurred. Cite packet numbers and stream indices.

Parse extension detail with:

```bash
openssl x509 -in cert.pem -noout -text
```

Keep full command output in `cases/<case>/extracted/` and summarize only the relevant
fields in notes or findings.

## Conclusions

Separate three questions: whether the certificate was valid at the observation time,
whether it names the intended peer, and whether a client actually enforced validation. A
self-signed certificate is not automatically a vulnerability in a pinned private
deployment, and a publicly trusted certificate does not prove the client checked it.

If private key material is found, record only its path, fingerprint or public-key digest,
provenance, and access restrictions. Never copy the key into `FINDINGS.md`.
