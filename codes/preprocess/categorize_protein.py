"""Load prepared patent-local chain classifications for extraction."""

import json
import os
from collections import Counter

import pandas as pd
from langgraph.graph import END, START, StateGraph

from ..base import BaseNode
from ..state import ProteinCategoryState, State


class ANARCIINode(BaseNode):
    """Load a frozen ANARCII result supplied in the prepared input package."""

    def __init__(self, input_dir):
        self.name = "ANARCIINode"
        self.input_dir = input_dir

    def load_result(self, patent_id):
        file_path = os.path.join(self.input_dir, f"{patent_id}.json")
        with open(file_path, "r", encoding="utf-8") as handle:
            result = json.load(handle)
        return pd.DataFrame(result["sequences"]).T

    def execute(self, state=ProteinCategoryState) -> ProteinCategoryState:
        frame = self.load_result(state["patent_id"])
        frame["category"] = frame["category"].str.replace("K", "L")

        idx_dict = frame.groupby("category").apply(lambda group: group.index.tolist()).to_dict()
        expected = [
            "VH",
            "VL",
            "HC",
            "LC",
            "scFv",
            "FC",
            "MS",
            "NB",
            "nonAB",
            "short",
            "etc",
        ]
        for key in expected:
            idx_dict.setdefault(key, [])
            idx_dict[key] = sorted(int(value) for value in idx_dict[key])
        return {"df_anarci": frame, "idx_dict": idx_dict}


def convert_state(state: State) -> ProteinCategoryState:
    return {"patent_id": state["patent_id"], "doc_type": state["doc_type"]}


class SelectEpsNode(BaseNode):
    def __init__(self, min_eps):
        self.name = "SelectEpsNode"
        self.min_eps = min_eps

    def execute(self, state=ProteinCategoryState) -> ProteinCategoryState:
        keys = ["VH", "VL", "HC", "LC", "scFv", "FC", "MS"]
        gaps = []
        for key in keys:
            indexes = state["idx_dict"].get(key, [])
            gaps.extend(right - left for left, right in zip(indexes[:-1], indexes[1:]))
        if gaps:
            most_common_gap, _count = Counter(gaps).most_common(1)[0]
            eps = max(most_common_gap + 1, self.min_eps)
        else:
            eps = self.min_eps
        return {"eps": eps}


def build_protein_categorization_graph(config):
    workflow = StateGraph(ProteinCategoryState)
    workflow.add_node("convert_state", convert_state)
    workflow.add_node(
        "load_anarcii", ANARCIINode(input_dir=config["io"]["anarcii"])
    )
    workflow.add_node(
        "select_eps",
        SelectEpsNode(min_eps=config["protein_category"]["select_eps"]["min_eps"]),
    )
    workflow.add_edge(START, "convert_state")
    workflow.add_edge("convert_state", "load_anarcii")
    workflow.add_edge("load_anarcii", "select_eps")
    workflow.add_edge("select_eps", END)
    return workflow.compile()
