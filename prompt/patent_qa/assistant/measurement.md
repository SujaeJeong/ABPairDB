# Summary of Key Measurement Values in Purified Antibody Binding Affinity Analysis

When evaluating the binding affinity of purified antibodies or antibody fragments, several parameters are commonly used. These values quantify the strength and characteristics of antibody-antigen interactions, with each metric reflecting different experimental methods and interpretations. It is especially important to understand the distinction between affinity (the strength of a single binding interaction) and avidity (the combined strength of multiple interactions).

Below is a concise summary of representative metrics—**KD**, **k<sub>on</sub>**, **k<sub>off</sub>**, **IC50**, and **EC50**—including their definitions, units, typical experimental techniques, and points to consider.

---

## KD (Equilibrium Dissociation Constant)

**Definition:**

KD is the equilibrium dissociation constant that describes the degree to which an antibody and antigen dissociate at equilibrium. It is defined as k<sub>off</sub> / k<sub>on</sub> and can also be interpreted as the concentration at which half of the antibody-antigen complexes are dissociated. A lower KD value indicates stronger binding (higher affinity), while a higher KD suggests lower affinity.

**Unit:**

KD is expressed in molar concentration (M), commonly as nM or μM. (Strictly, it is dimensionless, but concentration units are used by convention.)

**Measurement Techniques:**

Real-time interaction analysis methods such as surface plasmon resonance (SPR) and bio-layer interferometry (BLI) are widely used to measure KD. These methods determine k<sub>on</sub> and k<sub>off</sub> to calculate KD or directly measure KD based on equilibrium binding. Other techniques include isothermal titration calorimetry (ITC), equilibrium dialysis, and microscale thermophoresis (MST). Apparent KD values can also be estimated from antigen-antibody binding curves in ELISA or FACS experiments.

**Points to Consider:**

Avidity effects must be considered. For example, bivalent IgG antibodies can bind two antigens simultaneously, leading to higher effective binding stability compared to monovalent interactions. Thus, KD values measured under multivalent conditions (e.g., on cell surfaces) can appear much lower than the intrinsic 1:1 affinity. It is important to note differences between measurement formats; for example, KD values measured using Fab fragments (monovalent) versus full IgG (bivalent) may differ. Typically, KD is reported as a single binding value using methods like SPR/BLI, and should not be directly compared to KD values estimated from ELISA or FACS curves. A low KD indicates strong binding, but the value may vary depending on the measurement method and conditions.

---

## k<sub>on</sub> (Association Rate Constant)

**Definition:**

k<sub>on</sub> is the association rate constant that reflects how quickly the antibody and antigen form a complex. A higher k<sub>on</sub> value means the antibody and antigen bind rapidly, representing the frequency at which they encounter each other and form a complex per unit time and concentration. kon and ka both refer to the association rate constant and are equivalent concepts.

**Unit:**

Expressed as M<sup>-1</sup>s<sup>-1</sup> (per molar per second). In biological systems, k<sub>on</sub> typically ranges from 10<sup>3</sup> to 10<sup>7</sup> M<sup>-1</sup>s<sup>-1</sup> and is theoretically limited by molecular diffusion.

**Measurement Techniques:**

k<sub>on</sub> is determined using real-time interaction analysis (e.g., SPR, BLI), by fitting the binding curve from sensorgrams during the association phase. It cannot be directly obtained from equilibrium data such as standard ELISA or FACS; time-resolved kinetic experiments are required.

**Points to Consider:**

A high k<sub>on</sub> indicates rapid initial binding, but overall affinity depends on both k<sub>on</sub> and k<sub>off</sub>. Differences in k<sub>on</sub> among antibodies are relatively limited due to diffusion constraints, and high-affinity antibodies often differ more in k<sub>off</sub> than k<sub>on</sub>. Multivalent interactions complicate interpretation. Comparing k<sub>on</sub> values is meaningful only under identical conditions, as temperature and technique can influence results.

---

## k<sub>off</sub> (Dissociation Rate Constant)

**Definition:**

k<sub>off</sub> is the dissociation rate constant, representing how quickly the antibody-antigen complex dissociates over time. A lower k<sub>off</sub> means the complex is more stable and persists longer. For example, if k<sub>off</sub> = 1×10<sup>-2</sup> s<sup>-1</sup>, about 1% of complexes dissociate per second. The half-life of the complex can be estimated as t<sub>1/2</sub> ≈ 0.693/k<sub>off</sub>. kd and k<sub>off</sub> both refer to the dissociation rate constant and represent the same value. 

**Unit:**

Expressed as s<sup>-1</sup> (per second). Typical values range from 10<sup>-1</sup> to 10<sup>-6</sup> s<sup>-1</sup>, spanning very fast to very slow dissociation.

**Measurement Techniques:**

k<sub>off</sub> is measured using real-time interaction analysis (SPR, BLI), by fitting an exponential decay to the signal decrease during the dissociation phase. For very slow dissociation, extended stability tests or residence time measurements may be needed.

**Points to Consider:**

k<sub>off</sub> is a key indicator of binding durability. Antibodies with low k<sub>off</sub> values tend to form stable complexes and have high affinity (low KD). Therapeutic antibodies often require long residence times (low k<sub>off</sub>) for optimal in vivo efficacy. If dissociation is extremely slow, accurate measurement may be difficult. Multivalent antibodies may show biphasic dissociation, and k<sub>off</sub> determined from such systems can underestimate the true rate; therefore, monovalent fragments (such as Fab) are recommended for measuring true k<sub>off</sub> values.

---

## IC50 (Half-Maximal Inhibitory Concentration)

**Definition:**

IC50 is the concentration of an inhibitor (such as an antibody or drug) required to reduce a specific biological function by 50%. In simple terms, it is the antibody concentration needed to halve the activity or interaction of the target. IC50 is a standard indicator of inhibitor potency; a lower IC50 means higher potency.

**Unit:**

Expressed as a concentration, usually in M (nM, μM, etc.). Sometimes presented as mass/volume (e.g., μg/mL), but often converted to molarity for comparison.

**Measurement Techniques:**

IC50 is determined using dose-response curves by treating samples with various antibody concentrations and measuring the reduction in a target response (e.g., enzyme activity, cell proliferation, ligand-receptor binding). Competitive binding assays (e.g., competitive ELISA) and cell-based functional assays are common. For example, the IC50 of a neutralizing antibody is defined as the concentration required to neutralize 50% of viral activity.

**Points to Consider:**

IC50 is highly dependent on experimental conditions and does not directly reflect intrinsic binding affinity. The same antibody can have different IC50 values depending on cell type, substrate concentration, or assay readout. Avidity effects also matter: bivalent IgG antibodies may exhibit much lower IC50 values than monovalent Fab fragments due to cross-linking or multivalent binding. IC50 is a relative measure of inhibitory function under specific conditions and should not be confused with KD. A lower IC50 indicates greater effectiveness in that experiment but does not always mean stronger binding affinity.

---

## EC50 (Half-Maximal Effective Concentration)

**Definition:**

EC50 is the concentration of an activator (e.g., an agonist or activating antibody) required to achieve 50% of the maximal effect. It is the antibody concentration needed to elicit half of the maximal response in a biological system. A lower EC50 means the molecule is more effective at lower concentrations.

**Unit:**

Expressed in molarity (nM, μM, etc.), similar to IC50. In vivo, EC50 may be discussed as ED50 (effective dose) or as plasma concentration, but in vitro, molarity is standard.

**Measurement Techniques:**

EC50 is determined by dose-response experiments. In cell-based assays, different concentrations of antibody are applied to measure changes in cellular function (e.g., proliferation, differentiation). The concentration corresponding to 50% of the maximum response on the curve is defined as the EC50.

**Points to Consider:**

EC50 reflects functional potency in a specific experimental context, so values are not always directly comparable between systems. For example, an antibody may have an EC50 of 1 nM in one cell line, but a different value in another or in vivo. Avidity can also influence EC50; bivalent IgG antibodies may activate signaling more effectively and have lower EC50 values than monovalent Fab fragments. EC50 is a measure of relative functional effect in a given assay, not an absolute indicator of binding strength. As with IC50, EC50 should not be confused with KD; a low EC50 means strong effect in the tested system, but not necessarily the highest binding affinity.

---

## Rmax (Maximum Binding Response)

**Definition:**

Rmax is the maximum fitted binding response or sensor-surface capacity reported by SPR or BLI. It is an independent quantitative endpoint and must not be interpreted as KD, affinity, or potency.

**Unit:**

Rmax is commonly expressed in response units (RU).

**Points to Consider:**

Report Rmax as written when it is explicitly associated with an antibody-antigen experiment. Do not infer Rmax from a response curve, and do not compare its numeric value directly with concentration-based endpoints.
