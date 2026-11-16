"""Shared, side-effect-free metrics for experiment extraction evaluation.

The extraction-specific normalization happens in :mod:`codes.eval.exp_converter`
and :mod:`codes.eval.extractor`.  This module only decides which normalized rows
represent distinct experiments and performs a symmetric one-to-one comparison.
"""

from collections import deque

import pandas as pd


MAJOR_MEASUREMENTS = frozenset({"KD", "IC50", "EC50"})
CORE_COLUMNS = ["ag_rep_name", "standard_value", "standard_measurement"]
SEQ_COLUMNS = ["heavy_seq_id_no", "light_seq_id_no"]
NAME_COLUMN = "ab_rep_name"
REQUIRED_COLUMNS = CORE_COLUMNS + SEQ_COLUMNS + [NAME_COLUMN]


def _is_blank(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().lower() in {"", "none", "nan", "<na>"}


def _canonical(value):
    """Return a hashable representation with all missing markers collapsed."""
    return None if _is_blank(value) else value


def ensure_experiment_columns(df):
    """Return a copy containing every comparison column, including for 0 rows."""
    if df is None:
        df = pd.DataFrame()
    out = df.copy()
    for column in REQUIRED_COLUMNS:
        if column not in out.columns:
            out[column] = pd.Series([None] * len(out), index=out.index, dtype=object)
    return out


def filter_major_experiments(df):
    """Keep rows eligible for the headline binding-affinity evaluation."""
    out = ensure_experiment_columns(df)
    return out[out["standard_measurement"].isin(MAJOR_MEASUREMENTS)].copy()


def split_figure_excluded_rows(df):
    """Split validation rows into scored and figure-only subsets.

    Curators retained some labels for audit purposes while marking them with
    ``exclusion=figure`` because the source figure was not legible enough for a
    reliable extraction evaluation.  The tag has appeared with different
    capitalization, so comparison is deliberately case-insensitive.
    """
    out = ensure_experiment_columns(df)
    if "exclusion" not in out.columns:
        return out, out.iloc[0:0].copy()
    exclusion = out["exclusion"].fillna("").astype(str).str.strip().str.casefold()
    is_figure = exclusion.eq("figure")
    return out[~is_figure].copy(), out[is_figure].copy()


def _identity(row):
    """Identity used to remove repeated copies of one normalized experiment.

    A usable sequence form is the strongest identity.  Name is only used when
    both sequence identifiers are missing; this avoids collapsing two distinct
    name-only antibodies into one ``(None, None)`` sequence tuple.
    """
    core = tuple(_canonical(row[column]) for column in CORE_COLUMNS)
    seq = tuple(_canonical(row[column]) for column in SEQ_COLUMNS)
    if any(value is not None for value in seq):
        return ("seq",) + core + seq
    name = _canonical(row[NAME_COLUMN])
    if name is not None:
        return ("name",) + core + (name,)
    return ("unidentified",) + core


def deduplicate_experiments(df):
    """Deduplicate normalized experiments while retaining their full columns."""
    out = ensure_experiment_columns(df)
    if out.empty:
        out["_experiment_identity"] = pd.Series(dtype=object)
        return out
    identities = [_identity(row) for _, row in out.iterrows()]
    keep = []
    seen = set()
    for pos, identity in enumerate(identities):
        if identity not in seen:
            seen.add(identity)
            keep.append(pos)
    out = out.iloc[keep].copy().reset_index(drop=True)
    out["_experiment_identity"] = [identities[pos] for pos in keep]
    return out


def _keys(row):
    core = tuple(_canonical(row[column]) for column in CORE_COLUMNS)
    seq = tuple(_canonical(row[column]) for column in SEQ_COLUMNS)
    name = _canonical(row[NAME_COLUMN])
    seq_key = core + seq if any(value is not None for value in seq) else None
    name_key = core + (name,) if name is not None else None
    return seq_key, name_key


def _maximum_matching(adjacency, n_right):
    """Deterministic Hopcroft-Karp maximum-cardinality bipartite matching."""
    n_left = len(adjacency)
    left_match = [-1] * n_left
    right_match = [-1] * n_right
    distance = [0] * n_left

    def bfs():
        queue = deque()
        found = False
        for left in range(n_left):
            if left_match[left] == -1:
                distance[left] = 0
                queue.append(left)
            else:
                distance[left] = -1
        while queue:
            left = queue.popleft()
            for right in adjacency[left]:
                other = right_match[right]
                if other == -1:
                    found = True
                elif distance[other] == -1:
                    distance[other] = distance[left] + 1
                    queue.append(other)
        return found

    def dfs(left):
        for right in adjacency[left]:
            other = right_match[right]
            if other == -1 or (
                distance[other] == distance[left] + 1 and dfs(other)
            ):
                left_match[left] = right
                right_match[right] = left
                return True
        distance[left] = -1
        return False

    while bfs():
        for left in range(n_left):
            if left_match[left] == -1:
                dfs(left)
    return left_match, right_match


def match_experiments(prediction, gold):
    """One-to-one match normalized major experiments.

    Rows match when antigen, standardized value, and standardized measurement
    agree and either the usable sequence form or the non-empty antibody name
    agrees.  Maximum-cardinality matching prevents one row from becoming more
    than one TP.  Sequence edges are ordered before name-fallback edges as a
    deterministic tie-break, but the cardinality is always maximal.

    Returns a dictionary containing deduplicated prediction/gold frames, matched
    row-index pairs, unmatched frames, and TP/FP/FN counts.
    """
    pred = deduplicate_experiments(filter_major_experiments(prediction))
    ref = deduplicate_experiments(filter_major_experiments(gold))

    seq_lookup = {}
    name_lookup = {}
    for right, (_, row) in enumerate(ref.iterrows()):
        seq_key, name_key = _keys(row)
        if seq_key is not None:
            seq_lookup.setdefault(seq_key, []).append(right)
        if name_key is not None:
            name_lookup.setdefault(name_key, []).append(right)

    adjacency = []
    for _, row in pred.iterrows():
        seq_key, name_key = _keys(row)
        candidates = []
        if seq_key is not None:
            candidates.extend(seq_lookup.get(seq_key, ()))
        if name_key is not None:
            candidates.extend(name_lookup.get(name_key, ()))
        adjacency.append(list(dict.fromkeys(candidates)))

    left_match, _right_match = _maximum_matching(adjacency, len(ref))
    pairs = [(left, right) for left, right in enumerate(left_match) if right != -1]
    matched_left = {left for left, _ in pairs}
    matched_right = {right for _, right in pairs}

    pred = pred.copy()
    ref = ref.copy()
    pred["_merge"] = ["both" if i in matched_left else "left_only" for i in range(len(pred))]
    ref["_merge"] = ["both" if i in matched_right else "right_only" for i in range(len(ref))]
    pred_unmatched = pred[pred["_merge"] == "left_only"].copy()
    gold_unmatched = ref[ref["_merge"] == "right_only"].copy()
    tp = len(pairs)
    fp = len(pred) - tp
    fn = len(ref) - tp
    return {
        "prediction": pred,
        "gold": ref,
        "matches": pairs,
        "prediction_unmatched": pred_unmatched,
        "gold_unmatched": gold_unmatched,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "n_prediction": len(pred),
        "n_gold": len(ref),
    }


def score_gold_annotated_case(prediction, gold, excluded_gold=None):
    """Match one case and mark whether it is eligible for metric aggregation.

    Validation experiment labels are not exhaustive across patents.  A case is
    therefore evaluable only when at least one normalized major gold experiment
    exists.  Predictions from a gold-empty case are retained as ``unjudged`` for
    coverage/audit purposes, but must not be added to the FP denominator.

    ``excluded_gold`` contains audit-only labels such as ``exclusion=figure``.
    In-scope gold is matched first.  Only still-unmatched predictions are then
    compared with excluded gold; matches at that second stage are ignored
    rather than counted as FP.  This ordering prevents an excluded duplicate
    from stealing a TP from an otherwise identical in-scope gold row.

    The returned dictionary contains the normal :func:`match_experiments`
    fields plus evaluation/coverage fields and the excluded rows.
    """
    result = match_experiments(prediction, gold)
    n_prediction_total = result["n_prediction"]

    excluded_match = match_experiments(
        result["prediction_unmatched"], excluded_gold
    )
    excluded_prediction_ids = set(
        excluded_match["prediction"].loc[
            excluded_match["prediction"]["_merge"].eq("both"),
            "_experiment_identity",
        ]
    )
    is_excluded_prediction = result["prediction"]["_experiment_identity"].isin(
        excluded_prediction_ids
    )
    result["prediction"] = result["prediction"].copy()
    result["prediction"].loc[is_excluded_prediction, "_merge"] = "excluded"
    result["prediction_excluded"] = result["prediction"][
        result["prediction"]["_merge"].eq("excluded")
    ].copy()
    result["prediction_unmatched"] = result["prediction"][
        result["prediction"]["_merge"].eq("left_only")
    ].copy()
    result["excluded_gold"] = excluded_match["gold"]
    result["n_excluded_gold"] = excluded_match["n_gold"]
    result["n_excluded_prediction"] = len(result["prediction_excluded"])
    result["n_prediction_total"] = n_prediction_total
    result["n_prediction"] = n_prediction_total - result["n_excluded_prediction"]
    result["fp"] = len(result["prediction_unmatched"])
    result["is_evaluated"] = result["n_gold"] > 0
    result["n_unjudged_prediction"] = (
        0 if result["is_evaluated"] else result["n_prediction"]
    )
    return result
