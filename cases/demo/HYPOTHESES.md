# Hypotheses: demo

Interpretations of the observations in `EVIDENCE.jsonl`: claims about what the evidence
*means*. A hypothesis is not a finding. It is promoted only after its falsification test
has been run and it survives. Always record the alternatives and the smallest test that
would refute it.

Format per hypothesis, see the `case-workflow` skill:

```
## H-NN: <one-line interpretation>

**Interpretation:** what the cited observations are claimed to mean
**Supported by:** O-NN, O-NN   (observation IDs from EVIDENCE.jsonl)
**Alternatives:** other explanations consistent with the same observations
**Falsification test:** the smallest procedure that would refute this, and its result
**Status:** open | supported | refuted | promoted to F-NN
```

---
