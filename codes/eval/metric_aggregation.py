"""Shared aggregation rules for entity-level validation metrics.

The validation rows use ``(case_id, true_positive, false_positive,
false_negative)`` tuples.  A case may have predictions only, gold records only,
both sides populated, or neither side populated.  The rules below keep those
coverage states explicit:

* prediction-only cases contribute false positives;
* gold-only cases contribute false negatives;
* both-empty cases are reported in coverage but excluded from score averages;
* macro precision and recall omit cases whose respective denominator is
  undefined; and
* macro F1 includes every non-empty case, assigning zero to one-sided cases.
"""


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def aggregate_entity_rows(rows):
    """Aggregate coverage-aware entity rows into pooled and macro metrics."""
    material_rows = [
        row for row in rows
        if int(row[1]) + int(row[2]) + int(row[3]) > 0
    ]
    if not material_rows:
        return None

    tp = sum(int(row[1]) for row in material_rows)
    fp = sum(int(row[2]) for row in material_rows)
    fn = sum(int(row[3]) for row in material_rows)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    precision_values = []
    recall_values = []
    f1_values = []
    for _case_id, both, left_only, right_only in material_rows:
        both = int(both)
        left_only = int(left_only)
        right_only = int(right_only)
        pred_den = both + left_only
        gold_den = both + right_only

        case_precision = both / pred_den if pred_den else None
        case_recall = both / gold_den if gold_den else None
        if case_precision is not None:
            precision_values.append(case_precision)
        if case_recall is not None:
            recall_values.append(case_recall)

        if case_precision is None or case_recall is None:
            case_f1 = 0.0
        elif case_precision + case_recall:
            case_f1 = (
                2 * case_precision * case_recall
                / (case_precision + case_recall)
            )
        else:
            case_f1 = 0.0
        f1_values.append(case_f1)

    return {
        "n": len(material_rows),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "wprecision": _mean(precision_values),
        "wrecall": _mean(recall_values),
        "wf1": _mean(f1_values),
        "n_precision": len(precision_values),
        "n_recall": len(recall_values),
        "n_f1": len(f1_values),
    }


def summarize_entity_coverage(rows, *, n_json, n_state):
    """Summarize four coverage states plus missing/error case counts."""
    counts = {
        "both_nonempty": 0,
        "gold_only": 0,
        "prediction_only": 0,
        "both_empty": 0,
    }
    for _case_id, both, left_only, right_only in rows:
        pred_count = int(both) + int(left_only)
        gold_count = int(both) + int(right_only)
        if pred_count and gold_count:
            counts["both_nonempty"] += 1
        elif gold_count:
            counts["gold_only"] += 1
        elif pred_count:
            counts["prediction_only"] += 1
        else:
            counts["both_empty"] += 1

    counts.update(
        n_json=int(n_json),
        n_state=int(n_state),
        n_missing_state=max(int(n_json) - int(n_state), 0),
        n_evaluated=(
            counts["both_nonempty"]
            + counts["gold_only"]
            + counts["prediction_only"]
        ),
        error=max(int(n_state) - len(rows), 0),
    )
    return counts
