from pydantic import BaseModel, Field, constr
from typing import Annotated, List, Dict, Annotated, TypedDict, Literal, Union
import pandas as pd # type: ignore
from langchain_core.documents import Document # type: ignore


class State(TypedDict): # type: ignore
    patent_id: Annotated[str, "patent id"]
    doc_type: Annotated[str, "Document Type"]
    title: Annotated[str, "Document Title"]


class Element(BaseModel):
    element_name: Annotated[
        str,
        Field(description="The label or recognized type of this element (e.g., 'SEQ ID NO', 'amino acid sequence').")
    ]
    value_type: Annotated[
        str,
        Field(description="The data type of this element (e.g., 'string', 'integer', 'float', 'sequence', etc.).")
    ]
    includes_seq_id_no: Annotated[
        bool,
        Field(description="Indicates whether this element includes a SEQ ID NO.")
    ]


class Column(BaseModel):
    column_header: Annotated[
        str,
        Field(description="The header (label/title/name) of the column as it appears in the HTML table.")
    ]
    examples: Annotated[
        List[str],
        Field(description="Up to 4 example entries from the cells of this column. If there is less than 4 examples report \'\'")
    ]
    elements: Annotated[
        List[Element],
        Field(
            description=(
                "An array of dictionaries describing the distinct pieces of information within this column.\n"
                "In many cases, there may be only one element (e.g., a single data type).\n"
                "However, sometimes multiple pieces of data can be combined into one column.\n"
                "Each element has 'element_name', 'value_type', 'includes_seq_id_no'."
            )
        )
    ]


class TableSummary(BaseModel):
    title: Annotated[
        str,
        Field(
            description="Title of the table (right after {index})."
        )
    ]
    columns: Annotated[
        List[Column],
        Field(description="A list of columns, each with its name, examples, and elements.")
    ]
    category: Annotated[
        Literal['sequence description', 'experiment result', 'etc'],
        Field(
            description=(
                "The category of the table. Must be one of: "
                "['sequence description', 'experiment result', 'etc'].\n"
                "- sequence description: Describes a specific sequence (e.g., antibody components).\n"
                "- experiment result: Summarizes experimental results in a tabular format.\n"
                "- etc: ETC."
            )
        )
    ]
    footnotes: Annotated[
        List[str],
        Field(
            description="A list of entities in the table footnotes. If none, return an empty list."
        )
    ]


class TableElement(State):
    id: Annotated[str, "html <tables> id attribute e.g. TABLE-US-00001"]
    index: Annotated[str, "Table index referred in document e.g. TABLE 9"]
    table_html: Annotated[str, 'html content of the table']
    related_contents: Annotated[List[str], "document content referring table"]
    split_docs: Annotated[List[str], "split table"]


class AbNameLocation(BaseModel):
    name_location: Annotated[
        str,
        Field(description="Antibody location in the HTML table")
    ]
    seq_id_no_location: Annotated[
        str,
        Field(description="SEQ ID NO location in the HTML table")
    ]
    relative_location: Annotated[
        Literal['name_first', 'seq_id_no_first', 'same_row', 'null'],
        Field(
            description=(
                "The relative location of antibody name and SEQ ID NO. Must be one of: "
                "['same_row', 'name_first', 'seq_id_no_first', 'null'].\n"
                "- same_row: Both appear in the same row.\n"
                "- name_first: Antibody name appears before SEQ ID NO in previous row.\n"
                "- seq_id_no_first: SEQ ID NO appears before antibody name in previous row.\n"
                "- null: Either name or SEQ ID NO is not found."
            )
        )
    ]
    explanation: Annotated[
        str,
        Field(description="Brief explanation of how you determined your answer")
    ]


class DocState(State):
    html_path: Annotated[str, "html input file path"]
    full_html: Annotated[str, "full html text for the document"]
    split_docs: Annotated[List[Document], "split document"] # type: ignore
    split_tables: Annotated[List[Document], "split table"]
    tables: Annotated[TableElement, "Tables in the document"]
    entities: Annotated[Dict[str, bool], "Entities to check in document"]
    meta_docs: Annotated[List[Document], "metadata combined document"]
    meta_tables: Annotated[List[Document], "metadata combined tables"]
    idx_dict: Annotated[Dict[str, List[int]], "categorized SEQ ID NO list"]
    combined_docs: Annotated[List[Document], "text and table combined document"]

class ProteinCategoryState(State):
    entrez_result: Annotated[Dict[int, Dict[str, str]], "entrez search result for each SEQ ID NO"]
    df_protein: Annotated[pd.DataFrame, "Pandas Dataframe"]
    df_anarci: Annotated[pd.DataFrame, "anarci result for protein SEQ ID NO"]
    idx_dict: Annotated[Dict[str, List[int]], "categorized SEQ ID NO list"]
    eps: Annotated[int, "clustering coefficient"]

class CompareState(State):
    plabdab_csv_path: Annotated[str, "plabdab_csv_path"]
    df_plabdab: Annotated[pd.DataFrame, "Pandas Dataframe result for plabdab"]
    json_path: Annotated[str, "json validation set result path"]
    val_AB: Annotated[pd.DataFrame, "Antibody Validation Set"]
    val_AG: Annotated[pd.DataFrame, "Antigen Validation Set"]
    val_pair: Annotated[pd.DataFrame, "Antibody Antigen Pair Validation Set"]
    alt_dict: Annotated[Dict[str, str], "Alternative protein name dictionary"]


class QAState(State):
    docs: Annotated[List[Document], "List of split documents"]
    context: Annotated[str, "context from retriever"]
    question: Annotated[str, "question for the task"]
    idx_dict: Annotated[Dict[str, List[int]], "categorized SEQ ID NO dictionary"]
    entities: Annotated[Dict[str, bool], "Entities to check in document"]