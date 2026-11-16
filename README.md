# ABPairDB

Patent-derived antibody-antigen information extraction software and prompts.
Repository: [SujaeJeong/ABPairDB](https://github.com/SujaeJeong/ABPairDB).

## Contents

- codes/preprocess/: patent text and table preprocessing.
- codes/rag/: antigen, antibody-pair, and measurement extraction.
- codes/eval/: matching and metric aggregation.
- prompt/: prompts, context templates, and few-shot examples.
- config/release.yaml: portable extraction settings.
- scripts/run_extraction.py: extraction from one prepared patent input.
- scripts/evaluate_validation.py: offline scoring of normalized JSONL records.
- docs/: prepared-input, output, and evaluation schemas.
- environment.yml: inherited dependency specification.
- SOURCE_MANIFEST.json and SHA256SUMS: snapshot hashes and checksums.

See [Companion data](docs/data_package.md) for the separately packaged results.
The companion Zenodo candidate includes 196 original manual annotation JSON
files (187 marked for extraction and 9 excluded by reference.extract).
Raw patent HTML and fixed benchmark predictions are not included.
The original annotations require normalization before use with the evaluator.

## Verify the packaged files

From the repository root on a system with GNU coreutils:

~~~bash
sha256sum --check SHA256SUMS
~~~

The checksums cover the published payload files. SOURCE_MANIFEST.json records
their sizes, hashes, and source-copy status. Both manifest files are excluded
from their own checksum inventory. These checks detect changes relative to
this snapshot; they do not verify model outputs or reproduce manuscript metrics.

## Installation and input

Clone the repository and create the environment:

~~~bash
git clone https://github.com/SujaeJeong/ABPairDB.git
cd ABPairDB
conda env create -f environment.yml
conda activate abpairdb
~~~

A fresh installation of these dependencies has not been validated during
packaging. Hosted extraction requires an API key and incurs API usage.
The reranker may download model weights.

Obtain patent documents separately and prepare the HTML, patent-local chain
classifications, and metadata described in [Prepared input](docs/prepared_input.md).
The public command does not acquire patents or generate chain classifications.
A current patent webpage may require markup preparation before use.

Validate input without an API call:

~~~bash
python scripts/run_extraction.py \
  --patent-id <PATENT_ID> --input-dir <PREPARED_INPUT_DIR> \
  --config config/release.yaml --validate-input
~~~

For extraction, set OPENAI_API_KEY in the process environment, then run:

~~~bash
python scripts/run_extraction.py \
  --patent-id <PATENT_ID> --input-dir <PREPARED_INPUT_DIR> \
  --config config/release.yaml --output predictions/<PATENT_ID>.json
~~~

The .env.example file lists the variable; the CLI expects it in the process
environment. See [Output schema](docs/output_schema.md).
The configuration records GPT-4.1 extraction, text-embedding-3-large embeddings,
FAISS/BM25 retrieval, and BAAI/bge-reranker-base reranking. These are snapshot
settings, not a guarantee of current hosted-model availability.

## Optional offline evaluation

Normalize the companion original annotation JSON files to the documented
JSONL contract and supply the corresponding predictions:

~~~bash
python scripts/evaluate_validation.py \
  --gold <GOLD_JSONL> --predictions <PREDICTION_JSONL> --output metrics.json
~~~

See [Validation schema](docs/validation_schema.md). Original annotation JSON
files are not interchangeable with the normalized JSONL contract.

## Reproducibility boundary

This package preserves a selected prepared-input release implementation.
It does not include the entire historical antigen-mapping, curation, or
downstream-training workflow. It is not a demonstrated end-to-end rebuild of
the companion dataset or a reproduction of manuscript metrics.
Hosted extraction has not been rerun during packaging.

The evaluator measures extraction agreement, not assay equivalence or
measurement reliability. Consult source patents for scientific interpretation.

## Citation and license

Author metadata and the repository URL are in CITATION.cff. A DOI, tagged
release version, and software/data licenses have not yet been assigned.
This repository currently contains no LICENSE file.
