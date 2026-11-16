# Input format instruction regarding patent

Patents are typically very long HTML documents, often spanning over 100 pages. 
Patents related to antibodies share the following characteristics:

- **SEQ ID NO**  
Important sequences (such as proteins and nucleic acids) are indexed by **SEQ ID NO**. 
We will extract antigens, antibodies, antibody components, and antibody-derived molecules indexed via SEQ ID NO.

- **Claims**  
This section contains the legal claims that define the scope the patent seeks to protect.

- **Abstract**  
A brief summary of the patent.

- **Summary (of the invention)**  
A concise description of the invention and its embodiments, often using phrases like "In one embodiment, –" to explain possible implementations. 
This typically includes multiple embodiments of an antibody targeting a particular molecule.

- **Examples**  
Various experiments demonstrating the performance or efficacy of the invention, typically found in the "Example" section.

## Text Preprocessing

Instead of including the entire patent document, the patent is restructured into a **“context”** via text preprocessing:

**1. Split Documents**  
Patents are split into chunks of ~ 6000 characters each.

**2. Metadata Annotation** 
Since a chunk is a partial segment of the document, metadata information is attached at the beginning of the chunk to help with understanding its content. And it is presented in the following format:
	```
	Headings:
	  Heading 3: Heading 3 title
	  Heading 4: Heading 4 title
	  Heading 5: Heading 5 title
	
	Column Structure:
	    Column number: column name
	    - Elements within the column and their data types
	      - Boolean if column contains SEQ ID NO
	    - Elements within the column and their data types
	      - Boolean if column contains SEQ ID NO
	
	Footnotes:
	  - Extra information regarding table
	```

  - **Headings**: Title(s) of the heading(s) containing the chunk
  - **Column structure**: Describes what kind of information each table column contains. The information for each coulmn is represented as follows:
  - **Footnotes**: If there are any footnotes in table, they are transcribed as it is. 

**3. Chunk Reconstruction**  
Each chunk is wrapped in a `<chunk>` tag. Chunks relevant to the query are retrieved and re-ranked, then arranged in a logical order to form a coherent context.

## Key Considerations in Understanding Tabular Data

HTML tables can obscure underlying data due to their structural complexity. 

### Ideal Structure
- Each column: Represent a single **element** (e.g., name, SEQ ID NO, amino acid sequence, value, or unit).
- Each row: Represent a single, complete data **entry**. 

However, tables often deviate from this ideal structure:

### Multiple Elements in a Single Column
Sometimes, multiple elements are combined within a single column. These elements typically appear in two formats:
  - **Delimited Format**: Multiple elements in the same row, separated by a specific delimiter. 
  - **Stacked Format**: Multiple elements spans across separate rows.

**Recommended Action:**
1. Refer to **"Column Structure"** part of **"Metadata Annotation"**. The elements in each columns are listed in that part.
2. Clearly identify delimiters or vertical stacks.   

### Single Entry in multiple rows
Tables contain multiple types of data:
  - Amino acid sequence, Nucleotide sequence are lengthy. 
  - SEQ ID NO, sequence type(amino acid or nucleotide), antibody component type(heavy chain, light chain, scFv), name are short. 

A single entry sometimes occupy multiple rows for readability, especially containing long sequences. 
  - The number of rows occupied by a single entry is determined by the longest content. 
  - The remaining parts of the entries are filled with blank cells. 

The table contents are aligned as following ways:
  - **Columns** typically bottom-aligned. Blank cells are at the top of the column name. 
  - **Cell contents** typically Top-aligned. Blank cells are at the bottom of the cell content.

**Recommended Actions:**
1. Focus on rows where the number of blank cells decrease.  
    - Cell contents are typically top aligned, and blank cells are located at the bottom of the cell content. 
    - All cells are filled at the rows where new entry starts. 
    - And blank cells diminish at the beginning of the new entry. 

2. Refer to `<entry>` tag
    - Rows presumed to belong to a single entry have been enclosed within an `<entry>` tag.

3. Check whether the entry is truncated or not in chunk. 
    - Especially, when cell ends with '-', or '_', it is likely that the entry continues onto the next row.