# Extraction output schema

`scripts/run_extraction.py` writes one UTF-8 JSON object per patent. The
top-level `schema_version` for the first release is `1.0`.

## Top-level fields

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Output contract version |
| `patent` | object | Publication identifier, title, and source URL |
| `run_configuration` | object | Public config path and external model identifiers |
| `antigens` | array | Structured antigen records |
| `antigen_accessions` | array | Accession mentions for antigens without local sequence IDs |
| `antibody_pairs` | array | Heavy/light patent-local sequence pairs |
| `measurements` | array | Named- or sequence-pair-linked quantitative records |

The output does not include prompts expanded with patent text, raw model
responses, embeddings, vector stores, or Python pickle objects.

## `patent`

| Field | Type |
|---|---|
| `publication_id` | string |
| `title` | string |
| `source_url` | string |

## `antigens`

Antigen records preserve the fields produced by the extraction pipeline. Common
fields are:

| Field | Description |
|---|---|
| `name` | Antigen name |
| `organism` | Source organism |
| `abbreviation` | Alternative short name |
| `seq_id_no` | Patent-local SEQ ID NO, or `null` |
| `state` | Soluble, membrane-bound, or another reported state |
| `mutation` | Reported mutation information |
| `oligomer` | Reported oligomeric state |
| `strain` / `subtype` | Pathogen-specific detail when available |

## `antibody_pairs`

| Field | Description |
|---|---|
| `pair_type` | `VH_VL`, `HC_LC`, `scFv`, `FC`, `NB`, or `MS` |
| `heavy_seq_id_no` | Patent-local heavy-chain SEQ ID NO |
| `light_seq_id_no` | Patent-local light-chain SEQ ID NO or `null` |
| `name` | Extracted antibody names as an array; empty for unnamed pairs |

## `measurements`

| Field | Description |
|---|---|
| `antibody_reference` | `named_antibody` or `sequence_pair` |
| `ag_idx` | Index into `antigens` |
| `ab_name` | Named antibody identifier, when present |
| `heavy_seq_id_no` / `light_seq_id_no` | Sequence-pair identity, when present |
| `measurement` | Measurement label as reported |
| `value` | Extracted value |
| `unit` | Extracted unit |
| `approximate value` | Boolean indicating whether the source explicitly marks the single numeric value as approximate |
| `reference` | Pipeline source-chunk reference |
| `antibody_format` | Reported molecular format, when available |
| `experiment_summary` | Concise assay-context summary |

Missing scalar values are encoded as JSON `null`; non-finite numeric values are
never emitted.

`approximate value` records a textual qualifier in the patent source. It does
not quantify experimental error or indicate whether a value was produced by a
particular assay. The extraction prompts retain explicitly approximate single
numeric values, but do not turn inequalities, ranges, or qualitative results
into single numbers.

Assay information, when recoverable, is summarized in `experiment_summary`.
Values reported from ELISA, FACS, cell-based, SPR, BLI, or other assay formats
may differ in meaning, precision, and biological context and should not be
treated as directly interchangeable solely because their `measurement` labels
match. The pipeline preserves reported context but does not independently
verify experimental precision or assign an assay-quality score.
