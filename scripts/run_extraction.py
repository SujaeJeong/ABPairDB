#!/usr/bin/env python3
"""Run the ABPairDB extraction pipeline on one prepared patent input."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
for import_path in (REPOSITORY_ROOT, REPOSITORY_ROOT / "codes"):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from codes.state import filter_antigen_indices, validate_ag_out_index


def _resolve_config_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute() or path.exists():
        return path.resolve()
    candidate = REPOSITORY_ROOT / path
    return candidate.resolve()


def _metadata_row(metadata_path: Path, patent_id: str) -> dict[str, str]:
    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"Patent_ID", "GBReference_title"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{metadata_path}: missing required columns {sorted(missing)}"
            )
        rows = [row for row in reader if row.get("Patent_ID", "").strip() == patent_id]
    if len(rows) != 1:
        raise ValueError(
            f"{metadata_path}: expected exactly one row for {patent_id}, found {len(rows)}"
        )
    return rows[0]


def validate_prepared_input(input_dir: Path, patent_id: str) -> dict[str, Any]:
    """Validate the release input contract without making an API call."""
    html_path = input_dir / "html" / f"{patent_id}.html"
    anarcii_path = input_dir / "anarcii" / f"{patent_id}.json"
    metadata_path = input_dir / "patent_metadata.csv"
    missing = [
        str(path)
        for path in (html_path, anarcii_path, metadata_path)
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError("missing prepared-input files: " + ", ".join(missing))

    html = html_path.read_text(encoding="utf-8")
    if not html.strip():
        raise ValueError(f"{html_path}: HTML is empty")
    if ".sub." in html or ".sup." in html:
        raise ValueError(
            f"{html_path}: unresolved .sub./.sup. markup; see docs/prepared_input.md"
        )

    with anarcii_path.open("r", encoding="utf-8") as handle:
        anarcii = json.load(handle)
    sequences = anarcii.get("sequences") if isinstance(anarcii, dict) else None
    if not isinstance(sequences, dict):
        raise ValueError(f"{anarcii_path}: root object must contain a sequences object")
    if not sequences:
        raise ValueError(f"{anarcii_path}: sequences is empty; at least one sequence is required")
    for seq_id_no, record in sequences.items():
        try:
            int(seq_id_no)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{anarcii_path}: non-integer SEQ ID NO {seq_id_no!r}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"{anarcii_path}: sequence {seq_id_no} must be an object")
        for field in ("sequence", "category"):
            if not record.get(field):
                raise ValueError(
                    f"{anarcii_path}: sequence {seq_id_no} is missing {field}"
                )

    metadata = _metadata_row(metadata_path, patent_id)
    return {
        "patent_id": patent_id,
        "title": metadata["GBReference_title"].strip(),
        "source_url": metadata.get("source_url", "").strip()
        or f"https://patents.google.com/patent/{patent_id}/en",
        "html": str(html_path),
        "anarcii": str(anarcii_path),
        "metadata": str(metadata_path),
        "n_sequences": len(sequences),
        "n_tables": html.casefold().count("<tables"),
    }


def _load_runtime_config(
    config_path: Path, input_dir: Path, work_dir: Path
) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"{config_path}: configuration root must be a mapping")
    config = copy.deepcopy(config)

    prompt_dir = REPOSITORY_ROOT / "prompt"
    example_dir = prompt_dir / "example"
    io = config.setdefault("io", {})
    io.update(
        html=str(input_dir / "html"),
        anarcii=str(input_dir / "anarcii"),
        ref_csv_path=str(input_dir / "patent_metadata.csv"),
        base_dir=str(REPOSITORY_ROOT),
        prompt=str(prompt_dir),
        example=str(example_dir),
        input_state=str(work_dir / "state"),
        output_state=str(work_dir / "state"),
    )
    assistant_dirs = config["qa"]["assistant"].setdefault("dirs", {})
    assistant_dirs.update(
        prompt=str(prompt_dir),
        example=str(example_dir),
        embedding=str(work_dir / "vectorstore"),
        output=str(work_dir),
    )
    return config


def _antigen_output(qa_state, ag_main_node):
    df_out = ag_main_node.merge_output(qa_state)
    return ag_main_node.convert_NA(df_out, cols=list(df_out.columns))


def _run_pipeline(
    patent_id: str, config: dict[str, Any], *, include_measurements: bool
) -> dict[str, Any]:
    from codes.preprocess.categorize_protein import build_protein_categorization_graph
    from codes.preprocess.split_docs import (
        GatherExpDocs,
        build_document_proprecessing_graph,
    )
    from codes.rag.assistant import Assistant
    from codes.rag.find_ab import (
        AbMergeNode,
        AbNameDupNode,
        AbNameNode,
        AbPairNamed,
        AbPairUnnamedNode,
    )
    from codes.rag.find_ag import (
        AgAccessionNode,
        AgDetailNode,
        AgMainNode,
        FindAgNode,
        SummaryNode,
    )
    from codes.rag.find_pair import (
        ExperimentSummary,
        PairAbNameExpNode,
        PairNoNameExpNode,
    )
    from codes.state import DocState, ProteinCategoryState, QAState, State

    state = State(patent_id=patent_id, doc_type="patent")
    category_state = ProteinCategoryState(**state)
    category_state = build_protein_categorization_graph(config).invoke(category_state)

    doc_state = DocState(
        patent_id=patent_id,
        doc_type="patent",
        idx_dict=category_state["idx_dict"],
    )
    doc_state = build_document_proprecessing_graph(config).invoke(doc_state)

    assistant = Assistant(**config["qa"]["assistant"])
    assistant.embed_documents(doc_state["combined_docs"])
    qa_state = QAState(
        patent_id=patent_id,
        doc_type="patent",
        idx_dict=category_state["idx_dict"],
        eps=category_state["eps"],
        entities=doc_state["entities"],
    )

    for node in (
        SummaryNode(assistant, **config["qa"]["summary"]),
        FindAgNode(assistant, **config["qa"]["ag"]),
        AgDetailNode(assistant, **config["qa"]["ag_detail"]),
    ):
        qa_state.update(node.execute(qa_state))

    ag_main_node = AgMainNode(assistant, **config["qa"]["ag_main"])
    qa_state.update(ag_main_node.execute(qa_state))
    qa_state["ag_out"] = _antigen_output(qa_state, ag_main_node)

    qa_state.update(
        AgAccessionNode(assistant, **config["qa"]["ag_accession"]).execute(qa_state)
    )
    ag_names = "\n".join(
        qa_state["ag_main"].get("name", pd.Series(dtype=str)).dropna().astype(str)
    )
    qa_state.update(
        AbNameNode(assistant, **config["qa"]["ab_name"], ag_name=ag_names).execute(
            qa_state
        )
    )
    qa_state.update(
        AbNameDupNode(assistant, **config["qa"]["ab_name_duplicated"]).execute(
            qa_state
        )
    )
    qa_state.update(AbPairNamed().execute(qa_state))
    qa_state.update(
        AbPairUnnamedNode(assistant, **config["qa"]["ab_pair_unnamed"]).execute(
            qa_state
        )
    )
    qa_state.update(AbMergeNode().execute(qa_state))

    if include_measurements:
        for document in doc_state["combined_docs"]:
            heading = document.metadata.get("Heading 5") or ""
            if "EXAMPLE" in heading.upper():
                document.metadata["Heading 4"] = "EXAMPLES"
        gather_exp_docs = GatherExpDocs()
        doc_state.update(gather_exp_docs.execute(doc_state))
        doc_state["binding_exp_dict"] = gather_exp_docs.filter_exps(
            doc_state["exp_dict"]
        )
        qa_state.update(
            ExperimentSummary(
                assistant, **config["qa"]["experiment_summary"], **config["io"]
            ).execute(doc_state)
        )
        qa_state.update(
            PairAbNameExpNode(
                assistant,
                **config["qa"]["pair_ab_name_experiment"],
                **config["io"],
            ).execute(qa_state, doc_state)
        )
        qa_state.update(
            PairNoNameExpNode(assistant, **config["io"]).execute(qa_state, doc_state)
        )
    else:
        qa_state["pair_ab_name_experiment"] = pd.DataFrame()
        qa_state["pair_no_name_experiment"] = pd.DataFrame()

    return {"qa": qa_state, "category": category_state, "document": doc_state}


def _json_safe(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return [_json_safe(record) for record in value.to_dict(orient="records")]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _flatten_pairs(pair_frames: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    records = []
    for pair_type, frame in pair_frames.items():
        for record in _json_safe(frame):
            records.append({"pair_type": pair_type, **record})
    return records


def _measurement_records(qa_state):
    ag_out = qa_state["ag_out"]
    validate_ag_out_index(ag_out)
    records, audits = [], {}
    for source, key in (
        ("named_antibody", "pair_ab_name_experiment"),
        ("sequence_pair", "pair_no_name_experiment"),
    ):
        frame = qa_state.get(key)
        if isinstance(frame, pd.DataFrame):
            if not frame.empty and qa_state.get(f"{key}_antigen_index_source") != "ag_out":
                raise ValueError(f"{key}: legacy or unknown antigen index source; re-extract before export")
            frame, audit = filter_antigen_indices(frame, ag_out)
            audits[source] = {
                "extraction": qa_state.get(f"{key}_antigen_index_validation"),
                "export": audit,
            }
            records.extend({"antibody_reference": source, **row} for row in _json_safe(frame))
    return records, audits


def build_public_output(
    patent_id: str,
    metadata: dict[str, Any],
    pipeline_state: dict[str, Any],
    config_path: Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    qa_state = pipeline_state["qa"]
    measurements, index_audits = _measurement_records(qa_state)
    try:
        public_config_path = str(config_path.relative_to(REPOSITORY_ROOT))
    except ValueError:
        public_config_path = config_path.name
    return {
        "schema_version": "1.0",
        "patent": {
            "publication_id": patent_id,
            "title": metadata["title"],
            "source_url": metadata["source_url"],
        },
        "run_configuration": {
            "config": public_config_path,
            "chat_model": config["qa"]["assistant"]["model"]["model_name"],
            "embedding_model": config["qa"]["assistant"]["embedding"][
                "embedding_model_name"
            ],
        },
        "antigens": _json_safe(qa_state["ag_out"]),
        "antigen_accessions": _json_safe(qa_state.get("ag_accession", pd.DataFrame())),
        "antibody_pairs": _flatten_pairs(qa_state["ab_merged"]),
        "measurements": measurements,
        "measurement_index_validation": index_audits,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patent-id", required=True)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--config", default="config/release.yaml")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument(
        "--skip-measurements",
        action="store_true",
        help="run antigen and antibody-pair extraction only",
    )
    parser.add_argument(
        "--validate-input",
        action="store_true",
        help="validate the prepared input and exit before any API call",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_dir = args.input_dir.resolve()
    config_path = _resolve_config_path(args.config)
    if not config_path.is_file():
        raise FileNotFoundError(config_path)
    metadata = validate_prepared_input(input_dir, args.patent_id)
    if args.validate_input:
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is required for extraction")
    if args.output is None:
        raise ValueError("--output is required unless --validate-input is used")

    output_path = args.output.resolve()
    work_dir = (
        args.work_dir.resolve()
        if args.work_dir
        else output_path.parent / ".abpairdb-work" / args.patent_id
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    config = _load_runtime_config(config_path, input_dir, work_dir)
    pipeline_state = _run_pipeline(
        args.patent_id, config, include_measurements=not args.skip_measurements
    )
    output = build_public_output(
        args.patent_id, metadata, pipeline_state, config_path, config
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(_json_safe(output), indent=2, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
