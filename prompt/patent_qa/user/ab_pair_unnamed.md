# Instruction
- In this step, you will be given **SEQ ID NO list** and **context**.
  1. SEQ ID NO list: SEQ ID NO list corresponds to {h_comp} ({h_key}).
  2. Context: Chunks referring {h_comp} ({h_key}) in the SEQ ID NO list and any of {l_comp} ({l_key}). 
- **Task**: Read the context and find the antibody {l_comp} ({l_key}) that pairs with each {h_comp} ({h_key}).

## Sequence Pairing
There are several ways to indicate that {h_comp} and {l_comp} form an antibody pair.
Below are three common patterns:
  - {h_comp} ({h_key}) SEQ ID NO: A and {l_comp} ({l_key}) SEQ ID NO: B are described as **a pair or combination**.
  - SEQ ID NO: A appears in the {h_comp} ({h_key}) column and SEQ ID NO: B appears in the {l_comp} ({l_key}) column as part of the **same table entry**.
  - {h_comp} ({h_key}) SEQ ID NO: A and {l_comp} ({l_key}) SEQ ID NO: B are described as **components of the same antibody**.

However, there are similar but **ambiguous** cases. Please consider the following distinction:
  - If {h_comp} ({h_key}) SEQ ID NO: A is a component of an antibody, and separately {l_comp} ({l_key}) SEQ ID NO: B is also a component of an antibody, **this does not necessarily mean** A and B are components of the **same antibody**.
  - If {h_comp} ({h_key}) SEQ ID NO: A, B, C, D, E are components of anti-{ag_name} antibodies, and {l_comp} ({l_key}) SEQ ID NO: F, G, H, I, J are also components of anti-{ag_name} antibodies. This does not **necessarily mean** that A and B forms antibody pair.

Therefore, you must distinguish between:
  - "A and B **together** are components of one antibody"
  vs.
  - "A is a component of an antibody" and "B is a component of an antibody" stated independently. In this case, it is unclear that if A and B forms antibody pair. 

When identifying antibody heavy and light chain pairs, NEVER assume pairing based solely on sequence homology or alignment. A sequence homologous to a heavy chain and a sequence homologous to a light chain do NOT automatically constitute a valid antibody heavy-light chain pair. Only explicitly annotated or experimentally validated heavy-light chain combinations should be reported as true pairs.

## Output Format
Report antibody pairs in **JSON format** each pairs containing two keys: `heavy_seq_id_no` and `light_seq_id_no`. 
- `heavy_seq_id_no`: SEQ ID NO for the {h_comp} ({h_key}). 
- `light_seq_id_no`: SEQ ID NO for the {l_comp} ({l_key}).

{example}
---
# Task
Let's begin to find antibody pair between {h_comp} ({h_key}) and {l_comp} ({l_key}).

## SEQ ID NO list
{heavy_idx_list}

## Context:
{context}

## Answer: