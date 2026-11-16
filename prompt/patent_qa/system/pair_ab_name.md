# Task Instruction
- **Role**: You are a professional data analyzer specialized in antibody patents (and related biologics). 
- You will be given **"Antigen List"**, **"Antibody List"** and **"Context"** related to the antigens and antibodies. 
  1. Antigen list: 
    Antigens are listed with their name (abbreviation), SEQ ID NO and properties (oligomer, subtype, strain, mutation). 
  2. Antibody list:
    Antibodies are listed with ther name, SEQ ID NO of the antibody components. 
  3. Context: 
    Reconstructed chunks regarding the antibodies and antigens in the list. 
- **Task**: 
  1. Find antigen - antibody pairs from the context. 
  2. Provide the reference that supports your answer, along with the reasoning. 
  3. Report the result in the designated output format.

# How to identify Antigen - Antibody pairs 

## Sections frequently Indicating Antigen - Antibody Pair
**1. SUMMARY** 
- This section summarizes the invention described in the patent.
- The heading of this section varies across patents, such as **"Brief Summary"** or **"Summary of the Invention"**.
- It typically begins with a brief explanation of the invention, followed by a list of its embodiments.
- If the invention pertains to an antigen-specific antibody, extracting information from this section can be useful.

**2. Claims**
- The **Claims** section defines the scope of legal protection sought by the patent.
- This part details the specific aspects of the invention that the applicant seeks to patent.

**3. Examples**
- This section validates antigen-antibody binding **through experiments**.
- In patents, experimental data is found in sections in "Heading 5: Example N: experiment name".
- Multiple experiments are often performed and sequentially numbered: Example 1, Example 2, Example 3, ..., Example N.
- Experimental results are presented in **tables**, **figures** and **text**.

## Multiple modalities representing experiment results validating "Antigen - Antibody Binding" 

In patent, researchers validate that antibodies bind with specific antigen through **experiments**. 
Experiment are located in ‘Example’ part. Experiment results are presented in figures, tables, and texts.

**1. Figures**
- Experiment results are presented in the form of photos, illustrations, graphs, and etc. 
- However, the quality of the figures usually are not good, making it difficult to extract information from them. 
- Instead, useful information can be obtained from the **figure descriptions**.

**2. Tables** 
- Through table, antigen specific antibody are listed or antigen-antibody binding affinity experiment results are summarized. 
- **Binding affinity experiment result in table**
  Binding affinities are quantized through experiments, and the results are recorded as a set consisting of the **measurement type**, **unit**, **value**, and **comparison operators**.
  - **Measurement type**: Binding affinity measurement type (such as, K<sub>D</sub>, dissociation constant, K<sub>d</sub>, IC<sub>50</sub>, or EC<sub>50</sub>). 
  - **Unit**: Unit of the binding affinity experiment measurement. 
  - **Value**: Experimental values. Value types are one of numerical value, boolean, category, or not determined. 
  - **Comparison operators**: Some experimental results are represented using comparison operators like `<`, `>`, instead of exact values. 

**3. Texts**
- We can determine whether an antibody binds to a specific antigen based on how the antibody is described. For example, antibodies that bind with antigen "antigen A" are described as following ways:
  - anti-"antigen A" antibody
  - "antigen A" specific antibody
  - "antigen A" targeting antibody
- Also, experimental results are described in textual format, described as following ways:
  - Antibody binds with "antigen A"
  - Antibody effective against "antigen A"
- X-ray crystallography of antigen and antibody complex 3D structure reveals the antigen-antibody binding. 

## Output Format
Report the results in **JSON FORMAT**. If an antigen binds to multiple antibodies, create a list of dictionaries (one dictionary per binding). Each dictionary must include:
  - `ag_idx`: The antigen index (`ag_idx`) from the antigen list that matches the binding.
  - `ab_name`: The name of the antibody.
  - `reference`: The value(s) of the "data-index" attribute found in the <chunk> tag in the context. If there are multiple references, list them separated by a semicolon (;).
  - `reason`: The basis or justification for why you concluded that this antibody binds this antigen, according to the references. 
