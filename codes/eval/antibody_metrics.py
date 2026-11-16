"""Coverage-aware exact sequence-pair metrics for antibody extraction."""

import pandas as pd


PAIR_COLUMNS = ["heavy_seq_id_no", "light_seq_id_no"]


def _blank(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().casefold() in {"", "none", "nan", "<na>"}


def _seq(value):
    if _blank(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _prepare(df):
    out = pd.DataFrame() if df is None else df.copy()
    for column in PAIR_COLUMNS:
        if column not in out.columns:
            out[column] = pd.Series([None] * len(out), index=out.index, dtype=object)
    out["_pair_identity"] = [
        (_seq(row[PAIR_COLUMNS[0]]), _seq(row[PAIR_COLUMNS[1]]))
        for _, row in out.iterrows()
    ]
    return out.drop_duplicates("_pair_identity").reset_index(drop=True)


def split_excluded_antibody_rows(gold):
    """Split all curator-excluded antibody rows, including ``figure`` labels."""
    out = _prepare(gold)
    if "exclusion" not in out.columns:
        return out, out.iloc[0:0].copy()
    excluded = (~out["exclusion"].map(_blank)).astype(bool)
    return out.loc[~excluded].copy(), out.loc[excluded].copy()


def score_antibody_case(prediction, gold):
    """Score one patent without dropping gold-only or prediction-only cases.

    In-scope gold has priority.  A still-unmatched prediction that matches an
    excluded gold pair is ignored rather than counted as a false positive.
    """
    pred = _prepare(prediction)
    scored_gold, excluded_gold = split_excluded_antibody_rows(gold)
    pred_keys = set(pred["_pair_identity"])
    gold_keys = set(scored_gold["_pair_identity"])
    excluded_keys = set(excluded_gold["_pair_identity"])

    matched = pred_keys & gold_keys
    ignored = (pred_keys - matched) & excluded_keys
    fp_keys = pred_keys - matched - ignored
    fn_keys = gold_keys - matched

    pred = pred.copy()
    pred["_merge"] = pred["_pair_identity"].map(
        lambda key: "both" if key in matched else (
            "excluded" if key in ignored else "left_only"
        )
    )
    scored_gold = scored_gold.copy()
    scored_gold["_merge"] = scored_gold["_pair_identity"].map(
        lambda key: "both" if key in matched else "right_only"
    )
    return {
        "prediction": pred,
        "gold": scored_gold,
        "excluded_gold": excluded_gold,
        "tp": len(matched),
        "fp": len(fp_keys),
        "fn": len(fn_keys),
        "n_prediction": len(pred_keys) - len(ignored),
        "n_prediction_total": len(pred_keys),
        "n_gold": len(gold_keys),
        "n_excluded_gold": len(excluded_keys),
        "n_excluded_prediction": len(ignored),
    }
