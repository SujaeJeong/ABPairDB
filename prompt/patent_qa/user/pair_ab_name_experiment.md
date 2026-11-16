# Extract antibody experiment result
- Role: Read the context regarding antibodies and antigens from the provided antigen list and antibody list.
And extract antigen - antibody binding experiment result (**measurement**, **value**, **unit**). 

In the antigen list, all antigens from the patents are given with their antigen index, name, organism, SEQ ID NO, state, complex information, and mutation information. 
While the antigens share some common properties, they also differ in specific ways. 
Clearly distinguish these differences so you can accurately determine which antigen is involved in each pair. 
When you report an antigen, include its `ag_idx` (antigen index).

In the antibody list, partial antibody information is provided, including each antibody’s name and the SEQ ID NO of its components. 
Again, clearly distinguish any differences so you can accurately determine which antibody is involved in each pair. 
When you report an antibody, include its `ab_name`.


## Output Format
Report the results in **JSON FORMAT**. If an antigen binds to multiple antibodies, create a list of dictionaries (one dictionary per binding). Each dictionary must include:
- `ag_idx`: The antigen index (`ag_idx`) from the antigen list that matches the binding.
- `ab_name`: The name of the antibody.
- `measurement`: Experiment measurement (e.g. KD, Kd, IC50, EC50, etc.)
- `value`: numerical value of the measurment. 
- `unit`: unit of the value.
- `reference`: Extract "data-index" attribute values in the <chunk> tag in the context. If there are multiple references, list all and separate by semicolon(;).

---

## Context:
{context}

## Antigen:
{antigen}

## Antibodies:
{antibody}

## Answer: