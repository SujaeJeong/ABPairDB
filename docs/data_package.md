# Companion result data

The separate Zenodo candidate contains the following tables.

| File | Data rows |
| --- | ---: |
| final/exp_KD.csv | 8,543 |
| final/exp_IC50.csv | 3,867 |
| final/exp_EC50.csv | 2,990 |
| final/record_index.tsv | 15,400 |
| final/antigens.tsv | 2,680 |
| extraction/linked_extraction_records.tsv | 39,654 |
| extraction/final_record_links.tsv | 56,727 |

All seven tables are tab-delimited, including the .csv files. The index is a
lookup table, not additional measurements. Antigen metadata include 2,670
UniProtKB-target rows and 10 UniParc-target rows, not unique accession counts.

mean_log_value_nM is a mean of log10(nM). Exponentiating base 10 gives a
geometric mean in nM. The extraction table is normalized and sequence-attached,
not untouched LLM responses. Sequence/type links are many-to-many candidates,
not exact execution lineage.

The data package includes a data dictionary, exact column schemas, a patent
lookup index, provenance, and checksums. Lookup URLs are generated from
identifiers, not verified acquisition URLs. The validation/ directory contains
196 original annotation JSON files: 187 have reference.extract=true and 9
have reference.extract=false. Its README and index document the preserved
snapshot and exclusions. These are not normalized evaluator JSONL files.
Fixed benchmark predictions are not included. No Zenodo DOI is assigned here.
