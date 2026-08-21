---
name: traffic-analysis
description: Analyze captured or live network traffic to recover protocol structure and assess transport and application-layer cryptography, including TLS parameters, custom framing, and encrypted payloads. Use whenever working with a pcap or capture file, reverse engineering a wire protocol, examining a TLS handshake, or investigating how an application protects data in transit.
---

# Traffic analysis

Capture files go in `cases/<case>/artifacts/`. Reading a pcap is local work and needs no
authorization gate. Generating traffic against a live host does, so check `SCOPE.md`
first.

## Survey before drilling

```bash
capinfos <cap>.pcapng                                  # duration, packet count, size
tshark -r <cap> -q -z io,phs                           # protocol hierarchy
tshark -r <cap> -q -z conv,tcp                         # conversations by volume
```

The protocol hierarchy is the most informative first command: it tells you immediately
whether you are looking at TLS, a plaintext protocol, or something the dissectors do not
recognize. The third case is where the interesting work is.

Delegate the survey to the `traffic-triage` subagent for large captures. Packet lists
consume context quickly and are rarely needed in full.

## TLS

```bash
tshark -r <cap> -Y 'tls.handshake.type==1' -T fields \
  -e tls.handshake.version -e tls.handshake.extensions_server_name \
  -e tls.handshake.ciphersuite
tshark -r <cap> -Y 'tls.handshake.type==11' -T fields -e x509sat.printableString
```

What matters for a finding: the negotiated version and cipher suite, whether the
certificate chain validates, whether the client offers deprecated suites, and whether any
connection falls back to plaintext on error. TLS 1.2 with a modern AEAD suite is not a
finding. TLS 1.0, RC4, static RSA key exchange, or a self-signed chain accepted without
pinning are.

To decrypt, prefer a key log file (`SSLKEYLOGFILE`, then Wireshark's `tls.keylog_file`
preference) over an RSA private key. Key logging works with forward-secret suites, which
private keys do not.

## Unknown protocols

When the dissectors show nothing, work structurally. Export one conversation's payload
and look at it directly:

```bash
tshark -r <cap> -q -z follow,tcp,raw,0
tshark -r <cap> -Y 'tcp.stream==0' -T fields -e data.data | head
```

Reconstruct framing in this order, since each step constrains the next:

1. Message boundaries. Fixed-length records, a length prefix (try 2- and 4-byte, both
   endiannesses, with and without the header counted), or a delimiter.
2. Constant fields. Bytes identical across all messages are magic values, version fields,
   or type tags. These give you the header layout.
3. Monotonic fields. Counters and timestamps, often the sequence number or nonce, which
   matters for the crypto assessment.
4. Variable-length remainder. The payload. Test its entropy: near 8.0 means encrypted or
   compressed, and structure means neither.
5. Trailing fixed-size field. A 16- or 32-byte trailer is a MAC or an authentication tag,
   and its presence or absence is itself a finding.

Write the recovered structure as a parser in `cases/<case>/scripts/`. A working parser
makes the analysis reproducible and usually pays for itself within the same engagement.

## Assessing payload cryptography

Apply `crypto-primitive-id` to the payload. Two checks are specific to traffic:

- Cross-message ciphertext repetition. Identical ciphertext for messages you believe are
  identical indicates ECB, a static IV, or nonce reuse. Compare records byte by byte
  rather than eyeballing them.
- Replay. If a captured message is accepted twice, there is no effective freshness.
  Confirm this structurally from the capture, such as a repeated counter accepted by the
  server, rather than by replaying against a live host, which requires explicit
  authorization in `SCOPE.md`.

## Live interception

`mitmproxy` handles both capture and manipulation. Drive it via its Python API for
scripted analysis, and keep the session on the main thread since it holds live state.
Intercepting traffic you are not authorized to intercept is out of scope: the target must
appear in `SCOPE.md` before the proxy goes up.
