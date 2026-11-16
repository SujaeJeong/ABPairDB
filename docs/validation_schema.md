# Offline validation JSONL schema

`scripts/evaluate_validation.py` reads normalized gold and prediction records in
plain JSONL or gzip-compressed JSONL. Every line is one JSON object.

## Common fields

| Field | Gold | Prediction | Description |
|---|---:|---:|---|
| `case_id` | required | required | Stable validation-case identifier |
| `task` | required | required | `antigen`, `antibody_pair`, or `measurement` |
| `system` | omitted | required | Prediction system identifier |
| `empty` | optional | optional | `true` registers an evaluated case with no record |
| `exclusion` | optional | omitted | Curator exclusion label |

An `empty: true` marker carries only the common fields. It is useful for
preserving the denominator when a case has no gold or no predictions.

## Antigen records

```json
{"case_id":"case-001","task":"antigen","ag_rep_name":"CCR4"}
```

`ag_rep_name` is the frozen representative name produced during benchmark
normalization. The evaluator performs exact matching on this field; it does not
rerun name normalization.

## Antibody-pair records

```json
{"case_id":"case-001","task":"antibody_pair","heavy_seq_id_no":"6","light_seq_id_no":"5"}
```

Pairs are deduplicated by the two patent-local sequence identifiers. A
prediction matching an excluded gold pair is ignored rather than counted as a
false positive.

## Measurement records

```json
{"case_id":"case-001","task":"measurement","ag_rep_name":"CCR4","heavy_seq_id_no":"6","light_seq_id_no":"5","ab_rep_name":"MAB 1","standard_value":2.19,"standard_measurement":"KD"}
```

Required normalized fields are:

- `ag_rep_name`;
- `heavy_seq_id_no` and `light_seq_id_no`, which may be `null` for a name-only
  antibody;
- `ab_rep_name`, which may be `null` when sequence identity is available;
- `standard_value`; and
- `standard_measurement`.

The headline evaluator retains only `KD`, `IC50`, and `EC50`. Rows match when
antigen, standardized value, and standardized measurement agree and either the
sequence pair or non-empty antibody name agrees. Maximum-cardinality one-to-one
matching prevents one record from producing multiple true positives.

Measurement predictions in cases with no eligible measurement gold are
reported as unjudged and do not enter the false-positive denominator. This is
specific to the incompletely annotated measurement task; antigen and
antibody-pair prediction-only cases remain false positives.

This evaluator checks record-level agreement under the frozen normalization and
matching rules. It does not estimate experimental uncertainty, weight records
by assay modality, or establish that values from ELISA, FACS, cell-based, SPR,
BLI, and other assay formats are quantitatively interchangeable. The benchmark
metrics therefore evaluate extraction agreement, not assay precision or the
scientific equivalence of measurements across experimental platforms.

## Multiple systems

One prediction file can contain multiple systems:

```json
{"case_id":"case-001","task":"antigen","system":"abpairdb","ag_rep_name":"CCR4"}
{"case_id":"case-001","task":"antigen","system":"plabdab","ag_rep_name":"CCR4"}
```

The output contains a separate summary for each `system` and task, including
pooled metrics, macro metrics, TP/FP/FN, coverage states, excluded rows, and
unjudged measurement predictions.
