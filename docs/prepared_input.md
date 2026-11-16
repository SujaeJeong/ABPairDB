# Prepared input contract

ABPairDB extraction begins from a locally prepared patent package. Acquisition
of patent documents and generation of ANARCII chain classifications are not
performed by the public command.

## Directory structure

```text
<PREPARED_INPUT_DIR>/
├── patent_metadata.csv
├── html/
│   └── <PATENT_ID>.html
└── anarcii/
    └── <PATENT_ID>.json
```

`<PATENT_ID>` must be identical in the command line, both filenames, and the
metadata table.

## Patent HTML

`html/<PATENT_ID>.html` must be UTF-8 and must contain the complete cleaned text
needed for extraction. The file should retain:

- `<heading>` labels or already reconstructed `<h4>`/`<h5>` headings;
- `<tables id="TABLE-...">` wrappers and their table contents;
- patent-local SEQ ID NO mentions; and
- repaired `<sub>` and `<sup>` markup.

Legacy `.sub.` and `.sup.` placeholders are rejected by `--validate-input`.
This makes a run depend on a frozen local input rather than on a mutable live
patent webpage.

## Chain-classification JSON

`anarcii/<PATENT_ID>.json` must contain a `sequences` object keyed by patent-local
SEQ ID NO. Each record must contain at least `sequence` and `category`:

```json
{
  "sequences": {
    "1": {
      "sequence": "EVQLVESGGGLVQPGGSLRLSCAAS...",
      "category": "VH"
    },
    "2": {
      "sequence": "DIQMTQSPSSLSASVGDRVTITC...",
      "category": "VL"
    }
  }
}
```

Supported categories used by the pipeline include `VH`, `VL`, `HC`, `LC`,
`scFv`, `FC`, `MS`, `NB`, `nonAB`, `short`, and `etc`.

## Metadata CSV

`patent_metadata.csv` requires these columns:

```csv
Patent_ID,GBReference_title,source_url
US00000000A1,Example patent title,https://patents.google.com/patent/US00000000A1/en
```

`source_url` is optional. If it is absent or blank, the output uses the standard
Google Patents URL constructed from `Patent_ID`.

## Validation

Run the structural checks before setting an API key:

```bash
python scripts/run_extraction.py \
  --patent-id <PATENT_ID> \
  --input-dir <PREPARED_INPUT_DIR> \
  --validate-input
```

The command checks filenames, the unique metadata row, JSON structure, required
chain fields, unresolved markup, sequence count, and local table count. It does
not assess whether the source document or chain classifications are
scientifically correct.

