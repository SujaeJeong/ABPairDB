# Background information regarding Antibodies

An antibody (immunoglobulin, Ig) is a Y-shaped protein produced by the immune system to recognize and bind specific antigens, such as bacteria or viruses. Antibodies are composed of four polypeptide chains: two heavy chains and two light chains, which pair to form the characteristic Y-shaped structure. The “arms” of the Y are called the variable regions (V), which bind specifically to antigens, while the “stem” is the constant region (C), which interacts with immune cells. They play a crucial role in protecting the body from infections and are widely used in research and diagnostic applications. 

## Antibody Component

Understanding the antibody’s Fab region (arms), Fc region (stem), hinge region (the flexible area connecting the heavy chains), and individual domains of the heavy and light chains (VH, VL, CH1, CH2, CH3) is crucial for grasping how various antibody formats (full-length IgG, Fab fragments, scFv, nanobodies, diabodies, bispecific antibodies, etc.) are structurally organized. 

### Basic Structure and Components of Antibodies

**Immunoglobulin G (IgG) antibodies** have a Y-shaped structure made up of two heavy chains and two light chains. At the N-terminus of both chains are variable regions (V) that bind to diverse antigens, while the C-terminus of the heavy chains contains the constant region (C), which determines the antibody’s class and effector functions. 

The **Fragment of antigen binding** (abbreviation: **Fab**) consists of a heavy-light chain pair and serves as the antigen-binding site. Fab regions are is the arm region of the IgG antibodies, while the Fc region is tail part of antibody, formed by the joining of the constant regions of the two heavy chains and performs functions such as binding to Fc receptors on immune cells. 

The two **heavy chains** (abbreviation: **HC**) are connected by disulfide bonds at the hinge region, providing the arms (Fab) with flexibility and mobility.

There are five types of heavy chains (γ, α, μ, δ, ε), which determine the antibody isotype: IgG, IgA, IgM, IgD, and IgE, respectively. Light chains are of two types, κ and λ, and any given antibody has two identical light chains of only one type. Each heavy and light chain contains a **variable domain** (**VH** or **VL**) at the N-terminus and a **constant domain** (**CH** or **CL**) at the C-terminus. 

In IgG heavy chains (γ chains), the constant region is composed of three immunoglobulin domains (CH1, CH2, CH3), with a flexible hinge region between CH1 and CH2. Each IgG heavy chain is organized as VH–CH1–hinge–CH2–CH3, and two heavy chains connect at the hinge to form the complete Y shape. Each light chain consists of one VL and one CL domain, and both light chains are always of the same type (κ or λ).

The VH domain of the heavy chain and the VL domain of the light chain pair up to form the antigen-binding site at the tip of the Fab fragment, which is called the **Fragment of variable** (**Fv**) or **paratope**. 

**Complementarity-Determining Regions (CDRs)** are short, highly variable sequences located in the variable regions of an antibody’s heavy and light chains. These regions form the antibody’s antigen-binding site, which attaches to specific parts of an antigen. Each variable region of the heavy and light chains contains three CDRs, known as CDR1, CDR2, and CDR3. 

A Fab fragment contains the full VH–VL region needed for antigen binding, but not all variable regions of the antibody are the Fab; the Fab also includes some constant region sequences (part of CH1, CL), while the true variable regions are limited to the VH and VL domains at the Fab tip. 

The Fc fragment, on the other hand, consists of the C-terminal portions of both heavy chains (CH2, CH3), and is nearly identical in sequence among antibodies of the same isotype. 

The remaining CH domains of the antibody molecule constitute the constant region, which mediates effector functions by interacting with complement proteins or Fc receptors on immune cells.

The **Fragment of crystallizable** (abbreviation: **Fc**) region is highly conserved and readily crystallizes; it binds to Fc receptors on the surface of immune cells such as macrophages to mediate processes like phagocytosis and antibody-dependent cellular cytotoxicity (ADCC), and activates the complement system.

Antibodies can be cleaved into two regions by enzymatic digestion. For example, treating IgG with the protease papain splits the upper two arms into separate Fab fragments and leaves the lower stem as the Fc fragment. Papain cuts above the hinge-region disulfide bonds, so each Fab fragment contains the N-terminal part of one heavy chain (up to CH1) and the entire light chain.

This modular structure, divided into Fab and Fc, forms the basis for creating various antibody fragments and engineered formats.

## Antibody Formats

### **1. Single-chain Variable Fragment (scFv)**

**scFv (single-chain fragment variable)** is a 25~30 kDa polypeptide created by genetically linking the VH and VL regions with a short peptide linker. Although it lacks the Fc region, it preserves the identical antigen–binding site found in the original IgG, so its intrinsic affinity is usually unchanged.

- **Typical use:** early discovery and screening—especially phage display. After scFv clones are isolated, they are first checked by ELISA (phage- or soluble-scFv ELISA) and later reformatted into IgG.
- **Affinity assessment:** At the scFv stage most labs focus on “bind/no-bind” and rank order. ELISA confirms binding, while BLI or SPR can rank clones by off-rate. Because scFv is small, it is well suited for precise kinetic analysis by SPR/BLI (with optimized immobilization if needed).
- **Avidity note:** As a monovalent format, scFv shows no multivalent avidity, so its observed residence time is shorter than that of a bivalent IgG—but that reflects the true 1:1 affinity.
- **Workflow:** Hits are often triaged by ELISA/FACS/SPR at the scFv level, then converted to IgG for high-resolution affinity measurements. To cut cost and time, many groups now add high-throughput, real-time BLI screens directly at the scFv step to eliminate weak candidates early.

### **2. Fragment Antigen-Binding (Fab)**

A **Fab** (~50 kDa) consists of VH + CH1 (heavy chain) and the entire light chain (VL + CL), giving **one** antigen-binding site. Fab can be produced by enzyme digestion of IgG or by recombinant expression.

- **Why use Fab?** It removes bivalent avidity, so the measured KD truly reflects 1:1 binding. Vendor guides (e.g., Bio-Rad) recommend using monovalent fragments like Fab when comparing KD or IC₅₀ values across antibodies.
- **Assays:** Fab is routinely analyzed by SPR and BLI. Measuring Fab first, before IgG, prevents both arms of an IgG from binding simultaneously and lets you obtain the intrinsic KD of each paratope.
- **Signal considerations:** Because Fab is monovalent, assay signal can be weaker. In applications that need strong signals on fixed antigen (e.g., Western blot, FACS), a bivalent format (IgG or dimerized Fab) may perform better.
- **Trend:** Fab is preferred for quantitative KD comparison and structural studies, whereas IgG or multimeric derivatives are favored when high detection sensitivity or prolonged binding is needed.

### **3. IgG (Full-Length Immunoglobulin G)**

A full-length **IgG** (~150 kDa) is the natural H₂L₂ antibody with two identical antigen-binding sites (**bivalent**). Because of its Fc domain, IgG delivers effector functions and is the ultimate therapeutic format, so screening hits are eventually converted into IgG for characterization.

- **Direct measurement:** IgG affinity is usually measured by SPR or BLI; both yield kon, koff and KD. For mid-range affinities (nM–µM) the KD values from BLI and SPR agree closely.
- **Avidity effects:** When antigen is densely immobilized (SPR chip or ELISA plate), one IgG can grip two antigen molecules at once, slowing the apparent off-rate and lowering the apparent KD. Mitigate this by lowering ligand density or by measuring a monovalent fragment (Fab).
- **Importance:** Despite avidity complications, IgG data are essential because they reflect real-world binding strength—especially for multivalent cell-surface targets. Standard practice is to measure scFv/Fab affinities first, then confirm in IgG. Fc enables additional experimental options (Protein A/G capture, secondary-antibody detection), so IgG is compatible with many assay formats (SPR, BLI, ELISA, etc.).

### 4. Diabody (Bivalent scFv Dimer)

A **diabody** is an engineered dimer of two scFv units. Shortening the linker (≈5–10 aa) between VH and VL prevents intrachain pairing, forcing two scFv chains to pair intermolecularly as a **bivalent ~55–60 kDa dimer**.

- **Effect:** Bivalency greatly increases functional affinity (avidity); k_off drops sharply. Even a moderate-affinity scFv can behave like a high-affinity binder when formatted as a diabody.
- **Applications:** Useful for tumor targeting—smaller than IgG yet retaining long on-target residence time—and for imaging probes (good tissue penetration, rapid renal clearance).
- **Assays:** SPR/BLI quantify diabody binding but the KD reflects avidity, not intrinsic affinity. Researchers exploit this by designing diabodies with enhanced retention or by pairing two different scFvs to create bispecific binding.
- **Prevalence:** Still a specialized format; mainly used in engineering studies or niche therapeutics.

### 5. Nanobody (Single-Domain Antibody; sdAB)

A **nanobody** (abbreviation: **NB**) is a single VHH (camelid heavy-chain-only antibody domain) or occasionally a VL domain, ~12–15 kDa.

- **Affinity:** Despite its tiny size, a nanobody contains CDR loops enough to reach nM or even pM KD after optimization.
- **Assay tips:** Its small mass gives low RU on SPR; fix the nanobody to the chip or use BLI with the larger partner captured to boost signal.
- **Advantages:** High stability, easy engineering, cell penetration. Clinically validated (e.g., Caplacizumab). Overall, nanobody affinities often rival Fab for the same epitope.

### 6. Bispecific Antibody (bsAb)

A **bispecific antibody** simultaneously recognizes two distinct antigens. Architectures vary: asymmetric IgG, Fab-scFv fusion, BiTE (scFv×2), dual Fab fusion, etc. 

- **Affinity measurement:** Determine KD for target A and target B separately (SPR/BLI). Confirm **concurrent binding** via BLI sandwich or SPR dual-injection assays.
- **Assay mix:** Cell-based FACS validates simultaneous binding on native targets; functional assays measure biological activity.
- **Strategy:** Each arm is often tuned individually—sometimes one arm is purposely lowered in affinity to reduce side effects—so assays must characterize both arms plus their simultaneous engagement. Development pipelines therefore combine multiple formats (scFv, Fab, IgG) and assays (BLI, SPR, ELISA, FACS) at different stages.

## Antibody Affinity Measurement Methods

A variety of biophysical and immuno-analytical techniques are used to quantify antibody–antigen binding affinity.  Because each method differs in physical principle, sensitivity and throughput, researchers select tools according to experimental goals and antibody format.  Below, the three most common techniques—**SPR, BLI and ELISA**—are outlined first, followed by several auxiliary methods.

---

### 1. Surface Plasmon Resonance (SPR)

- Any real-time binding study that measures refractive-index changes on a gold film qualifies as SPR. The best-known implementation is **Biacore** (Cytiva; formerly GE Healthcare).
- **Principle & read-out** – A partner (antibody or antigen) is immobilized on a gold film; the other flows past in solution. Changes in surface refractive index are recorded as sensorgrams, yielding **association and dissociation rate constants (k_on, k_off)** and the **equilibrium constant (KD)**.
- **Performance** – Detects interactions from high pM to low µM with excellent sensitivity and reproducibility; long regarded as the *gold standard* for accurate KD determination, especially for therapeutic leads.
- **Format flexibility** – Works with anything from tiny scFv/nanobody fragments to full IgG and bispecifics. Experimental strategy is adjusted by format:
    - Small analytes (scFv, nanobody) are usually **immobilized** to maximize signal.
    - Multivalent IgG calls for low ligand density to avoid avidity artefacts or, alternatively, parallel Fab measurements for intrinsic affinity.
- **Strengths & limitations** – Capable of tracking very slow off-rates (pM binders) over minutes to hours, but traditional instruments analyze one channel at a time and are expensive. New multichannel systems (e.g., high-throughput Carterra SPR) now allow dozens to hundreds of antibodies to be profiled in parallel. SPR generally requires purified samples, so it is favored for detailed characterization rather than early crude screening. Real-time kinetics also help rank candidates by off-rate, a key developability attribute.

---

### 2. Bio-Layer Interferometry (BLI)

- **Principle & hardware** – Uses fibre-optic sensor tips (e.g., ForteBio Octet). Analyte binding alters optical interference at the tip surface, giving a real-time signal akin to SPR but without flow channels or gold chips.
- **High throughput** – 8-, 16-, 96- or 384-sensor formats enable rapid screening of hundreds to thousands of clones. Common workflow: quick BLI screen → shortlist → high-precision SPR.
- **Sample tolerance & cost** – No microfluidics means viscous or crude matrices (cell-supernatant, serum) can often be analyzed after simple dipping and rinsing. Instruments and consumables cost less than SPR.
- **Accuracy** – For typical nM–low µM interactions, BLI and SPR produce nearly identical KD values and rankings. Caveats:
    - Ultra-tight binders (sub pM range) may suffer drift or mass-transport limits.
    - Very weak interactions (> µM) can be noisy compared with SPR.
- **Trends** – Increasingly used for early hit ranking (especially scFv obtained by phage display) because BLI can capture subtle kinetic differences missed by ELISA. Also supports concurrent-binding assays for bispecifics, competition or blocking studies, and other formats requiring higher throughput.

---

### 3. Enzyme-Linked Immunosorbent Assay (ELISA)

- **Role** – Classic solid-phase assay detecting bound antibody via enzyme-labelled reporters; excels at **bulk, parallel screens**.
- **Workflow** – In phage-display projects, hundreds of scFv clones are first triaged by ELISA; the strongest signals progress to SPR/BLI.
- **Read-out** – Provides relative titres or **EC₅₀** values from dose–response curves. EC₅₀ often correlates with affinity but is **not** a true KD because avidity, secondary-antibody amplification and wash steps distort binding equilibria.
- **Limitations & best practice** – Very low-affinity antibodies may wash away (false negatives), whereas bivalent IgG can appear artificially strong. Competitive ELISA can rank affinities more accurately—within ~2-fold of SPR in some studies—but variability is method-dependent. For quantitative kinetics, ELISA results are normally validated by SPR or BLI.

---

### 4. Other Techniques

| Method | Typical Use-Case & Notes |
| --- | --- |
| **Flow Cytometry (FACS)** | Measures binding to **cell-surface antigens**; fluorescence vs concentration yields an EC₅₀.  Good for confirming that antibodies recognize native targets on cells, but EC₅₀ ≠ solution KD. |
| **Isothermal Titration Calorimetry (ITC)** | Solution-phase thermodynamic profile (ΔH, ΔS, KD) with no immobilization.  Needs high-purity, high-concentration samples; less sensitive for very tight binders.  Mostly used for in-depth mechanistic studies. |
| **Microscale Thermophoresis (MST)** | Fluorescently labelled partner + temperature gradient; works with low sample volumes and complex matrices.  Suitable for nM–µM affinities, but labelling and very fast kinetics can be challenging. |
| **QCM, GCI, acoustic, SwitchSENSE, etc.** | Niche platforms; SPR/BLI remain the dominant standards for kinetic data in the 2020s. |

---

### Preference by Development Stage

| Stage | Favored Formats | Favored Methods |
| --- | --- | --- |
| **Massive primary screen** | scFv, Fab, Nanobody | ELISA, high-throughput BLI |
| **Detailed hit characterization** | IgG | SPR, BLI |
| **Intrinsic affinity comparisons** | Monovalent Fab / scFv | SPR, BLI (1:1 model) |
| **Functional / cell assays** | IgG, bispecifics, multimers | FACS, neutralization, plus SPR/BLI cross-checks |

### Utilizing Fc region in the IgG antibodies

The Fc region of IgG provides unique experimental advantages that are not found in antibody fragments. By using Fc-binding proteins such as Protein A or G, IgG antibodies can be oriented and captured on the surface of laboratory devices. 

This approach allows for easy and rapid preparation without the need for direct chemical immobilization of the antibody, and if necessary, IgG can be released from the sensor by changing the pH, enabling the sensor to be reused. Additionally, secondary antibodies that recognize the Fc region of IgG can be used to amplify and detect signals. In indirect methods like ELISA and western blot, enzyme- or fluorophore-labeled secondary antibodies (such as anti-human IgG-HRP) bind to the primary IgG antibody, significantly boosting the detection signal. Since each Fc region of an IgG contains multiple epitopes, many secondary antibodies can bind to a single IgG, further increasing sensitivity.

In contrast, antibody fragments like Fab, which lack an Fc region, cannot use these standardized secondary antibody detection methods and require direct labeling or special tags, making experimental procedures more complicated. For these reasons, full-length IgG antibodies are highly compatible with a variety of experimental formats. Thanks to capture and detection methods that utilize the Fc region, IgG can be easily handled in most analytical platforms such as SPR, BLI, and ELISA.

## Methods for Obtaining Variable Region Sequences from Antibody Clones

Obtaining the variable region sequences of the heavy (VH) and light (VL) chains from antibody clones is an essential step for the recombinant production and patent filing of monoclonal antibodies. The precise identification of the VH/VL sequences, which determine the antibody’s binding sites, is crucial for maintaining affinity and specificity, as well as for further applications such as humanization or modification.

Here, we explain how to acquire these sequences from three major sources of antibody clones (hybridoma, phage display, and single B cell) and highlight best practices for obtaining accurate sequences.

---

### 1. Sequence Acquisition from Hybridoma-Based Clones

A hybridoma is a cell line created by fusing an immunized animal’s B cell with a myeloma cell, enabling continuous production of a specific monoclonal antibody. The general process of isolating and sequencing the **antibody genes (heavy and light chains)** from these cells is as follows:

**RNA Extraction and cDNA Synthesis:**

First, total RNA is extracted from hybridoma cells, and an RT (reverse transcription) reaction is performed to synthesize cDNA using antibody mRNA as a template. Typically, primers targeting the constant regions of the heavy and light chains are used to separately generate cDNA for each chain. For example, in mouse hybridomas, complementary primers for the IgG heavy chain, kappa light chain, and lambda light chain are prepared so that three separate cDNA synthesis reactions can be performed from a single RNA sample. This allows for both kappa and lambda light chain types to be covered if the specific light chain of the clone is unknown.

**PCR Amplification (Variable Region Amplification):**

Using the synthesized cDNA as a template, PCR is performed to amplify the variable regions (VH, VL) of the heavy and light chains. Because hybridoma antibody variable regions are highly diverse, it is difficult to design universal primers. Traditionally, a mix of several degenerate primer sets targeting the 5’ leader sequence or the framework 1 (FR1) region is used. While this degenerate primer approach has a success rate of about 80–90%, some clones (10–20%) may experience non-specific amplification or failure, and there may be amplification of residual myeloma-derived Ig genes.

To address these issues, 5’ RACE (Rapid Amplification of cDNA Ends) methods, which attach polyA tails or adapters to the 5’ end of cDNA, are also used, though the process is more complex and time-consuming.

Recently, template-switching RT-PCR technologies like SMART have been introduced. These methods add a universal sequence to the 5’ end during reverse transcription, allowing all desired variable regions to be amplified using just one universal 5’ primer and a nested 3’ primer targeting the constant region. For example, during RT, specific primers for the constant regions of IgG, kappa, and lambda, along with a template-switch oligo, are used, so only one primer pair per chain (universal 5’ primer + nested 3’ constant region primer) is needed to efficiently amplify VH or VL. PCR products are typically around 500–600 bp, covering the variable region (~350 bp) and some constant region sequence.

**Sequence Analysis:**

The PCR-amplified variable region fragments are purified and sequenced, typically using Sanger sequencing if a single-band PCR product is obtained. Sometimes, PCR products are cloned into T-vectors for sequencing to detect/eliminate PCR-introduced mutations. Once both heavy and light chain sequences are obtained, they are combined to deduce the complete antibody amino acid sequence. The gene family and biological relevance can be checked via database searches (e.g., IgBLAST).

For example, the closest V, D, and J genes can be identified by comparing the sequence with human/mouse gene libraries, and suspicious mutations (e.g., nonsense codons) can be checked.

**Functional Validation:**

It is important to verify that the obtained VH and VL sequences correspond to the actual antibody’s function. Typically, the heavy and light chain genes are inserted into recombinant expression vectors, and the produced recombinant antibody is tested for binding activity to its target. There are cases where recombinant antibodies produced from hybridoma-derived sequences have shown the same high affinity for the antigen as the original antibody, confirming the accuracy of the sequence. This reproducibility is especially important as evidence for the reliability of the sequence when preparing patent applications.

---

### 2. Sequence Acquisition from Phage Display-Derived Clones

Phage display is a technique in which antibody fragments (usually scFv single-chain or Fab fragments) are displayed on bacteriophages, enabling selection of clones that bind to the target. Selected phage clones contain the genetic information for the antibody fragment, so sequencing their DNA reveals the VH/VL sequences. The main steps are as follows:

**Obtaining Clone DNA:**

Selected clones from phage display usually carry the antibody gene fragment on a phagemid plasmid. Plasmid DNA is extracted from E. coli cells infected with the phage, or replicative DNA is directly isolated from the phage particles. As the DNA contains known vector sequences, PCR and sequencing can be performed without a separate RT step.

**PCR and Sequencing:**

The inserted antibody fragment is either amplified by PCR or directly sequenced using universal primers (e.g., M13 forward/reverse, or T7/NdeI region primers on the vector). For scFv, where VH-linker-VL is encoded as a single gene, a single sequencing read can cover the whole variable region, while for Fab fragments, both the heavy and light chain regions are sequenced separately. Sequencing is typically performed by Sanger method, and each clone’s plasmid is analyzed individually, making the process rapid. If sequencing dozens or hundreds of top clones after phage selection, multiple individual Sanger sequencing reactions are required, which can be laborious and limits sample throughput.

Recently, high-throughput sequencing (NGS) is being used for selected phage pools, allowing tens of thousands or millions of sequences to be read at once, and facilitating high-throughput discovery of top clones. However, because the accuracy of individual reads and the matching of heavy and light chains (pairing information) is critical, final candidates are usually reconfirmed by Sanger sequencing and subsequent functional validation.

**Sequence Confirmation and Application:**

Extract the VH and VL regions from the sequence data (both included in scFv) and translate to amino acid sequences. Antibody fragments obtained from phage display are often reformatted as full-length IgG for further development, which also requires genetic sequence information. The phage clone sequence is inserted into an IgG expression vector, and the binding properties of the expressed antibody are compared to the original phage-screened fragment.

While recombinant antibodies produced from scFv/Fab sequences usually retain antigen binding, changes in antibody format can affect affinity, so further characterization is required.

Best practice is to check phage-display-derived sequences for residual mutations or frameshifts (bidirectional sequencing as needed), and to validate binding activity and specificity using antibodies expressed and purified from the confirmed sequence. Especially in patent applications, data (e.g., antigen binding assay results) demonstrating the functional efficacy of the sequence should be provided.

---

### 3. Sequence Acquisition from Single B Cell-Derived Clones

Single B cell antibody acquisition technology isolates antigen-specific B cells from animals or humans, and directly obtains the antibody heavy and light chain genes from each cell using molecular biology techniques. Modern single B cell techniques typically use flow cytometry to isolate the desired B cells (e.g., antigen-binding memory B cells) at the single-cell level, then amplify the cell’s Ig genes by RT-PCR. Both sensitivity (due to the tiny amount of genetic material) and accuracy are critical. The general procedure is:

**Single-Cell cDNA Synthesis:**

Once a single cell is isolated, it is lysed to release mRNA and an RT reaction is performed. There are two approaches to primer selection during RT:

    (1) Use random hexamers to reverse-transcribe all cellular mRNA, followed by selective PCR amplification of Ig genes;

    (2) If the antibody class is known (e.g., IgG+ memory B cell), use constant region-specific primers to selectively synthesize Ig heavy/light chain cDNA.

The former is simple and unbiased but may reduce PCR efficiency due to non-specific cDNA, while the latter is targeted but may be less efficient if mRNA quantity is low. Heavy and light chains are always treated separately. Usually, cDNA synthesis and PCR for IgH, Igκ, and Igλ are prepared from each cell, to cover both light chain types (κ/λ)

**Nested PCR Amplification:**

Nested (two-step) PCR is performed using cDNA from a single cell as template to amplify the Ig variable regions. Many primer sets, designed for different species and gene families, are used (degenerate primers). For example, human/mouse VH primers target the leader sequence or FR1 region for each heavy chain family, with 3’ primers for IgM, IgG, or J-region sequences. After initial PCR, a second nested PCR is performed with internal primers to increase specificity. The final products are ~350 bp (heavy) and ~320 bp (light).

**Sequence Verification and Chain Pairing:**

Purified PCR products for the heavy and light chains are sequenced by Sanger method to obtain each cell’s antibody sequence. It is essential to verify that the heavy and light chains are paired from the same cell. If one chain fails to amplify, the antibody is incomplete, so only cells with both chains amplified are used for downstream processes. Sequence data are analyzed (e.g., by IgBLAST) for gene family and mutation checks, and for features such as somatic mutation rate and CDR3 length. Careful inspection is needed for possible PCR errors; if unexpected amino acid changes are found, PCR artifacts are suspected. Multiple or repeated sequencing is used for critical clones.

**Cloning and Functional Validation:**

The confirmed heavy and light chain genes are inserted into expression vectors to produce recombinant antibodies from single B cells. Sequence integrity is crucial, so it is recommended to confirm the vector sequence matches the original PCR sequence 100%. Vectors with sequence errors are discarded. The paired expression vectors are used to transfect cells and produce recombinant monoclonal antibodies, which are then tested for binding to the original antigen.

It is particularly important to confirm that the single B cell-derived antibody is functional; only clones that show positive binding to the antigen are used for further development or patenting. Patent applications must provide data confirming that the antibody binds the specific antigen with the required affinity and specificity.

---

### Best Practices for Accurate Sequence Acquisition and Validation

There are several best practices common to all the above methods to ensure the most accurate and reliable sequence acquisition—especially important for patent applications, where submitted sequences must be error-free and supported by functional validation:

**High-Fidelity Amplification and Error Monitoring:**

Use high-fidelity DNA polymerases when possible to minimize PCR-introduced mutations, but balance efficiency and accuracy when sample amounts are small. Carefully analyze sequencing results for suspicious substitutions by comparing with known germline sequences and/or independent amplification attempts.

**Primer Design and Use:**

Use validated primer sets for degenerate primers and maximize specificity with nested PCR. Aliquot primer mixes to avoid repeated freeze-thaw cycles, which degrade performance. For further accuracy, consider using custom primers based on sequencing results for a third PCR round.

**Heavy-Light Chain Pairing:**

Because both chains are required for a functional antibody, correctly identifying the light chain partner is crucial. For hybridomas, if the light chain type is unknown, amplify both kappa and lambda, but if the secreted antibody’s light chain is known, unnecessary reactions can be avoided. If both chain types are amplified, sequence/protein comparison or co-expression assays are used to identify the correct light chain.

**Multiple Sequence Verification and Preservation:**

Critical clones should be sequenced bidirectionally or redundantly to confirm accuracy. The final sequence in the expression vector should also be verified to match the original PCR product, avoiding patent submission of erroneous sequences.

Accurately archived sequences are essential for future antibody production and improvement, and can be used to restore antibodies if cell lines are lost due to senescence or genetic instability.

**Functional Validation:**

Finally, antibodies generated from the obtained VH/VL sequences should be functionally validated to ensure they retain the original clone’s properties. Data proving the antibody’s binding or neutralizing activity must accompany patent submissions. Only antibodies whose sequence and functional data match are considered valuable for patents, and thorough accuracy and validation at every step is crucial.