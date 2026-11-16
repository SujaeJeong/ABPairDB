#!/usr/bin/env python3
"""Recalculate ABPairDB validation metrics from fixed JSONL artifacts.

The evaluator is deliberately offline: it reads normalized gold and prediction
records, performs the frozen matching rules, and never imports extraction code
or calls an external model.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from codes.eval.antibody_metrics import score_antibody_case
from codes.eval.experiment_metrics import score_gold_annotated_case
from codes.eval.metric_aggregation import aggregate_entity_rows


SCHEMA_VERSION = "1.0"
TASK_ALIASES = {
    "antigen": "antigen",
    "antibody": "antibody_pair",
    "antibody-pair": "antibody_pair",
    "antibody_pair": "antibody_pair",
    "measurement": "measurement",
    "experiment": "measurement",
}
TASK_ORDER = ("antigen", "antibody_pair", "measurement")


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load plain or gzip-compressed JSONL with line-numbered errors."""
    source = Path(path)
    records = []
    with _open_text(source) as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{source}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{source}:{line_number}: each JSONL row must be an object")
            records.append(record)
    return records


def _blank(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().casefold() in {"", "none", "nan", "<na>"}


def _canonical_task(value: Any) -> str:
    key = str(value).strip().casefold()
    try:
        return TASK_ALIASES[key]
    except KeyError as exc:
        allowed = ", ".join(TASK_ORDER)
        raise ValueError(f"unsupported task {value!r}; expected one of: {allowed}") from exc


def _prepare_records(
    records: Iterable[dict[str, Any]], *, predictions: bool
) -> list[dict[str, Any]]:
    prepared = []
    for index, original in enumerate(records, start=1):
        record = dict(original)
        if _blank(record.get("case_id")):
            raise ValueError(f"record {index}: case_id is required")
        if _blank(record.get("task")):
            raise ValueError(f"record {index}: task is required")
        record["case_id"] = str(record["case_id"]).strip()
        record["task"] = _canonical_task(record["task"])
        record["empty"] = bool(record.get("empty", False))
        if predictions:
            system = record.get("system")
            if _blank(system):
                raise ValueError(f"prediction record {index}: system must not be blank")
            record["system"] = str(system).strip()
        prepared.append(record)
    return prepared


def _material(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if not record.get("empty", False)]


def _frame(records: Iterable[dict[str, Any]], columns: list[str]) -> pd.DataFrame:
    material = _material(records)
    rows = []
    for record in material:
        missing = [column for column in columns if column not in record]
        if missing:
            raise ValueError(
                f"{record['task']} case {record['case_id']}: missing fields {missing}"
            )
        rows.append({column: record.get(column) for column in columns + ["exclusion"]})
    return pd.DataFrame(rows, columns=columns + ["exclusion"])


def _score_antigen(prediction_records, gold_records) -> dict[str, Any]:
    pred = _frame(prediction_records, ["ag_rep_name"])
    gold = _frame(gold_records, ["ag_rep_name"])

    pred_names = {
        str(value).strip() for value in pred["ag_rep_name"] if not _blank(value)
    }
    if gold.empty:
        scored_names: set[str] = set()
        excluded_names: set[str] = set()
    else:
        is_excluded = ~gold["exclusion"].map(_blank)
        scored_names = {
            str(value).strip()
            for value in gold.loc[~is_excluded, "ag_rep_name"]
            if not _blank(value)
        }
        excluded_names = {
            str(value).strip()
            for value in gold.loc[is_excluded, "ag_rep_name"]
            if not _blank(value)
        }

    matched = pred_names & scored_names
    ignored = (pred_names - matched) & excluded_names
    return {
        "tp": len(matched),
        "fp": len(pred_names - matched - ignored),
        "fn": len(scored_names - matched),
        "n_prediction": len(pred_names) - len(ignored),
        "n_prediction_total": len(pred_names),
        "n_gold": len(scored_names),
        "n_excluded_gold": len(excluded_names),
        "n_excluded_prediction": len(ignored),
        "is_evaluated": True,
    }


def _score_antibody(prediction_records, gold_records) -> dict[str, Any]:
    columns = ["heavy_seq_id_no", "light_seq_id_no"]
    result = score_antibody_case(
        _frame(prediction_records, columns), _frame(gold_records, columns)
    )
    result["is_evaluated"] = True
    return result


def _score_measurement(prediction_records, gold_records) -> dict[str, Any]:
    columns = [
        "ag_rep_name",
        "heavy_seq_id_no",
        "light_seq_id_no",
        "ab_rep_name",
        "standard_value",
        "standard_measurement",
    ]
    prediction = _frame(prediction_records, columns)
    gold = _frame(gold_records, columns)
    if gold.empty:
        scored_gold = gold.copy()
        excluded_gold = gold.copy()
    else:
        is_excluded = ~gold["exclusion"].map(_blank)
        scored_gold = gold.loc[~is_excluded].copy()
        excluded_gold = gold.loc[is_excluded].copy()
    return score_gold_annotated_case(prediction, scored_gold, excluded_gold)


SCORERS = {
    "antigen": _score_antigen,
    "antibody_pair": _score_antibody,
    "measurement": _score_measurement,
}


def _coverage(case_results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "both_nonempty": 0,
        "gold_only": 0,
        "prediction_only": 0,
        "both_empty": 0,
    }
    for result in case_results:
        n_prediction = int(result["n_prediction"])
        n_gold = int(result["n_gold"])
        if n_prediction and n_gold:
            counts["both_nonempty"] += 1
        elif n_gold:
            counts["gold_only"] += 1
        elif n_prediction:
            counts["prediction_only"] += 1
        else:
            counts["both_empty"] += 1
    counts.update(
        n_cases=len(case_results),
        n_evaluated=sum(bool(result.get("is_evaluated", True)) for result in case_results),
        n_unjudged_predictions=sum(
            int(result.get("n_unjudged_prediction", 0)) for result in case_results
        ),
        n_excluded_gold=sum(int(result.get("n_excluded_gold", 0)) for result in case_results),
        n_excluded_prediction=sum(
            int(result.get("n_excluded_prediction", 0)) for result in case_results
        ),
    )
    return counts


def evaluate_records(
    gold_records: Iterable[dict[str, Any]],
    prediction_records: Iterable[dict[str, Any]],
    *,
    include_cases: bool = False,
) -> dict[str, Any]:
    """Evaluate in-memory records using the same contract as the CLI."""
    gold = _prepare_records(gold_records, predictions=False)
    predictions = _prepare_records(prediction_records, predictions=True)

    systems = sorted({record["system"] for record in predictions})
    if not systems:
        raise ValueError("predictions contain no system; add at least one record or empty marker")

    gold_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    prediction_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in gold:
        gold_groups[(record["task"], record["case_id"])].append(record)
    for record in predictions:
        prediction_groups[(record["system"], record["task"], record["case_id"])].append(record)

    output: dict[str, Any] = {"schema_version": SCHEMA_VERSION, "systems": {}}
    for system in systems:
        system_output = {}
        for task in TASK_ORDER:
            gold_cases = {
                case_id for task_name, case_id in gold_groups if task_name == task
            }
            prediction_cases = {
                case_id
                for system_name, task_name, case_id in prediction_groups
                if system_name == system and task_name == task
            }
            case_ids = sorted(gold_cases | prediction_cases)
            if not case_ids:
                continue

            case_results = []
            metric_rows = []
            for case_id in case_ids:
                result = SCORERS[task](
                    prediction_groups.get((system, task, case_id), []),
                    gold_groups.get((task, case_id), []),
                )
                summary = {
                    "case_id": case_id,
                    "tp": int(result["tp"]),
                    "fp": int(result["fp"]),
                    "fn": int(result["fn"]),
                    "n_prediction": int(result["n_prediction"]),
                    "n_gold": int(result["n_gold"]),
                    "n_excluded_gold": int(result.get("n_excluded_gold", 0)),
                    "n_excluded_prediction": int(
                        result.get("n_excluded_prediction", 0)
                    ),
                    "is_evaluated": bool(result.get("is_evaluated", True)),
                    "n_unjudged_prediction": int(
                        result.get("n_unjudged_prediction", 0)
                    ),
                }
                case_results.append(summary)
                if summary["is_evaluated"]:
                    metric_rows.append(
                        (case_id, summary["tp"], summary["fp"], summary["fn"])
                    )

            task_output = {
                "metrics": aggregate_entity_rows(metric_rows),
                "coverage": _coverage(case_results),
            }
            if include_cases:
                task_output["cases"] = case_results
            system_output[task] = task_output
        output["systems"][system] = system_output
    return output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, help="gold.jsonl or gold.jsonl.gz")
    parser.add_argument(
        "--predictions", required=True, help="predictions.jsonl or predictions.jsonl.gz"
    )
    parser.add_argument(
        "--output", default="-", help="output JSON path; use '-' for standard output"
    )
    parser.add_argument(
        "--include-cases", action="store_true", help="include per-case TP/FP/FN summaries"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = evaluate_records(
        load_jsonl(args.gold),
        load_jsonl(args.predictions),
        include_cases=args.include_cases,
    )
    payload = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output == "-":
        sys.stdout.write(payload)
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
