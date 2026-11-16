import pandas as pd

measurement_map = {}

measurement_map['KD'] = [
    'kD',
    'KD',
    'KD1',
    'KD (nM)',

    'KD dimeric',
    'KD monomeric',
    'KD (pH 6.0)',
    'KD (pH 7.4)',
    'KD (PACAP38)',
    'KD (PACAP27)',
    'KD (SET, Fab)',

    'KD (ELISA)',
    'ELISA KD',
    'MAb KD',
    'MAb ELISA KD',
    'KD @ 25°C (34mer)',
    'KD @ 37°C (34mer)',
    'KD @ 37°C (84mer)',
    'KD (BIACORE, Fab)',
    'KD (huPD-L1-his)',
    'KD (CynoPD-L1-his)',

    'SPR KD',
    'KD (Biacore)',
    'KD (BiaCore)',
    'KD (SET)',
    'KD (MSD)',
    'KD (ForteBio)',
    'KD (ELISA, human HER2)',
    'KD (JIMT-1 cell surface binding)',
    'KD (subtype A Prefusion)',
    'KD (subtype A Postfusion)',
    'KD (subtype B Prefusion)',
    'KD (subtype B Postfusion)',
    'KD subtype A Prefusion',
    'KD subtype B Prefusion',
    'KD subtype B Postfusion',
    'KD subtype A Postfusion',
    'KD (M) subtype A Prefusion',
    'KD (M) subtype A Postfusion',
    'KD (M) subtype B Prefusion',
    'KD (M) subtype B Postfusion',

    'KDapp',
    'KD,app',
    'KD_app',
    'KD app',
    'App. KD',
    'app KD',
    'Kd app',

    'Apparent KD',
    'KinExA KD',

    'KD (M) at 25°C (hGFRα3-mFc)',
    'KD (M) at 37°C (hGFRα3-mFc)',
    'KD (M) at 25°C (hGFRα3-mmH)',
    'KD (M) at 37°C (hGFRα3-mmH)',
    'KD (M) at 25°C (MfGFRα3-mmH)',
    'KD (M) at 37°C (MfGFRα3-mmH)',

    'KD (SPR, 214E)',
    'KD (SPR, 214K)',
    'KD (Cell Surface)',
    'KD (SPR, Cynomolgus)',

    'Affinity Biacore (KD)',


    'KD (25°C)',
    'KD (37°C)',
    'KD (CaCl2, Biacore)',
    'KD (MgCl2, Biacore)',
    'KD (FACS, HUVEC cells)',
    'KD (Prefusion subtype A)',
    'KD (Prefusion subtype B)',
    'KD (Postfusion subtype A)',
    'KD (Postfusion subtype B)',
    'KD (Octet, monovalent human CD38-HIS)',
    'KD (Biacore, monovalent human CD38-HIS)',

    'KD (Biacore, Human FcγRI)',
    'KD (Biacore, Human FcγRIIa/131H)',
    'KD (Biacore, Human FcγRIIa/131R)',
    'KD (Biacore, Human FcγRIII/158F)',
    'KD (Biacore, Human FcγRIII/158V)',
    'KD (Biacore, Murine FcγRI)',
    'KD (Biacore, Murine FcγRIII)',
    'KD (Biacore, Murine FcγRIV)',
    'KD (CaCl2)',
    'KD (MgCl2)',

    'SET KD',
    'KINEXA KD',
    'BIACORE KD',
    'Biacore KD',

    'K_D',
    'K_D Monomer',
    'K_D Dimer',
    'Solution K_D Monomer',
    'K_D (hIgG1)',
    'Cell Binding, K_D',
    'Biacore Human PD1 K_D',
    'Biacore Cynomolgus K_D',
    'Postfusion subtype A K_D',
    'Postfusion subtype B K_D',
    'Prefusion subtype A K_D',
    'Prefusion subtype B K_D',
    'K_D (Prefusion subtype A)',
    'K_D (Prefusion subtype B)',
    'K_D (Postfusion subtype A)',
    'K_D (Postfusion subtype B)',

    'Avg KD',

    'FACS KD',
    'S1 KD',
    'RBD KD',
    'KD (pH 5.8)',
    'KD Monomeric',
    'apparent KD',
    'KD @ 25° C.',
    'KD @ 37° C.',
    'KD @ 37° C. (84mer)',

    'Monovalent KD',
    'equilibrium KD',
    'KD(37° C.)',
    'KD (kin: koff/kon)',
    'KD (steady-state)',
    'K_D',
    'apparent solution equilibrium KD',
    'KD by SPR',
    'calc. KD',
    'KD pH 7.4',
    'KD pH 6.0',
    'Affinity KD',
    'KD (KinExA)',
    'ka (1/Ms) (pH 6.0)',
    'KD (M) (pH 6.0)',
    'cell based affinity hu CDH-3 KD',
    'cell based affinity mac CDH-3 KD',
    'Low resolution KD',
    'High resolution KD',
    'KD at 25° C.',
    'KD at 37° C.',
    'Kinetic KD',
    'solution KD',
    'apparent KD (VEGF:Flk-1 complex)',
    'Octet KD',
    'apparent KD FACS',
    'scFv KD',
    'IgG KD',
    'Microcal KD',
    'monovalent KD',
    'KD 7.4',
    'KD 5.8',
    'KD [Biacore]',
    'KD [ForteBio]',
    'KD (1:1 Langmuir)',
    'Fab KD human TREM2-Fc (M) Monovalent',
    'Fab KD',
    'cell binding huT2 BW K_D',
    'equilibrium binding constant',
    'equilibrium binding constant (deglycosylated hCD47)',
    'KD by Biacore',
    'KD (BIAcore)',
    'KD (Scatchard)',
    'KD(apparent)',
    'cell-surface KD',
    'KD (Octet)',
    'cell surface KD',

    'apparent KD (NCI-H929)',
    'apparent KD (MM.1S)',
    'apparent KD (Ad293 + huBCMA)',
    'in vivo KD',
    'apparent monovalent affinity (K_D)',
    'apparent monovalent KD',
    'KINEXA™ KD',
    'BIACORE™ KD',
    'KD (affinity - Octet)',
    'KD Ga',
    'KD Gb',
    'KD [pH 6.0]',
    'KD [pH 7.4]',
    'KD (M) (pH 7.4)',
    'KD (M) (pH 6.0)',
    'cell based affinity hu CDH-3 KD',
    'apparent KD FACS',
    'scFv KD',
    'affinity (Biacore KD)',
    'KD by Biacore',
    'cell surface KD',
    'K<sub>D</sub>',
    'affinity constant at equilibrium',
]

measurement_map['Kd'] = [
    'Kd',
    'K_d',
    'KDIS',
    'Kdiss',
    'Kd (BIAcore)',
    'Kd (Scatchard)',
    'FACS Kd',
    'ELISA Kd',
    'Kd (ELISA)',
    'Kd (SPR)',
    'Biacore Kd',
    'Kd (kinetic, SPR)',
    'Kd (equilibrium)',

    'apparent Kd',
    'Apparent Kd',

    'SPR Kd',
    'Kdis',
    'High affinity binding site Kd\'',
    'Low affinity binding site Kd\'',

    'apparent affinity constant (Kd)',

    'High affinity binding site Kd',
    'KD (nM, SPR)',
    'Kd (SET)',
    'Kd (Biacore)'
]

measurement_map['kd'] = [
    'kd',
    'kd (huPD-L1-his)',
    'kd (CynoPD-L1-his)',
    'kd (early, 10 s)',
    'kd (late, 50 s)',
    'kd (hIgG1)',
    'kd, app',
    'kd (PACAP38)',
    'kd (PACAP27)',
    'kd @ 25°C (34mer)',
    'kd @ 37°C (34mer)',
    'kd @ 37°C (84mer)',
    'kd (1/s) (pH 7.4)',
    'kd (1/s) (pH 5.0)',
    'kd (pH 7.4)',
    'kd (pH 5.0)',
    'kd (25°C)',
    'kd (37°C)',
    'BIACORE kd',
    'k_d',
    'kd (pH 5.8)',
    'kd @ 25° C. - 34mer',
    'kd @ 37° C. - 34mer',
    'kdis',
    'kdiss',
    'kdissoc',
    'kd (1/s) (pH 6.0)',
    'BLI binding (off rate kdis)',
    'dissociation constant',
    'dissociation rate (kd)',
    'apparent dissociation rate constant (kd)',
    'BIACORE™ kd',
    'k_diss',
    'kd @ 37° C. - 84mer',
    'k diss',
    'K<sub>d</sub>',
]

measurement_map['IC50'] = [
    'IC50',
    'IC-50',
    'IC50 (Elk1 luciferase reporter gene assay)',
    'HTRF Receptor Neutralisation IC50',
    'Primary T-cell Assay IC50',
    'IC50 (fibrils)',
    'IC50 (monomers)',
    'IC50 (sPD-L1/PD-1)',
    'IC50 (sPD-L2/PD-1)',
    'IC50 (ELISA)',
    'IC50 (STAT6 Bioassay)',
    'IC50 (TF1/A12 Bioassay)',
    'IC50 (STAT6 Bioassay, hIL-13)',
    'IC50 (TF1 Bioassay)',
    'IC50 (TF1 Bioassay, hIL-13)',
    'IC50 (STAT6 Bioassay, hIL-13 neutralization)',
    'IC50 (STAT6 Bioassay, hIL-4 neutralization)',
    'IC50 (TF1/A12 Bioassay, hIL-4 neutralization)',
    'IC50 (phospho-EGFR inhibition)',
    'IC50 (blocking SIRPα binding to CD47, IgG1 yeast)',
    'IC50 (blocking SIRPα binding to CD47, IgG4 CHO)',
    'Ca Flux IC50',
    'pERK IC50',
    'IC50 (no wash)',
    'IC50 (2-hours-wash)',
    'Chemotaxis IC50',
    'Calcium flux IC50',
    'IC50 (chemotaxis, IgG1 format, rhIP-10, 1 nM or 0.2 nM)',
    'IC50 (calcium flux, IgG1 format, rhIP-10, 10 nM)',
    'IC50 (chemotaxis, IgG1 format, native hIP-10, 0.6 nM)',
    'IC50 (chemotaxis, scFv format, hIP-10, 2 nM)',
    'IC50 (calcium flux, scFv format, hIP-10, 10 nM)',
    'IC50 (Chemotaxis)',
    'IC50 (Calcium flux)',
    'IC50 (Chemotaxis, IgG1 format, rhIP-10, 0.2 nM)',
    'IC50 (Calcium flux, scFv format, hIP-10, 10 nM)',
    'IC50 (Chemotaxis, scFv format, hIP-10)',
    'IC50 (Chemotaxis, scFv format, hIP-10, 2 nM)',
    'IC50 (Chemotaxis, IgG1 format, rhIP-10, 1 nM or 0.2 nM)',
    'IC50 (Chemotaxis, scFv format)',
    'IC50 (Calcium flux, scFv format)',
    'IC50 (Chemotaxis, IgG1 format)',
    'IC50 (Cell Proliferation Assay, Mouse Monocytic)',
    'IC50 (Human Whole Blood Monocyte Activation Assay)',
    'IC50 (Receptor Binding Inhibition Assay)',
    'IC50 (huPD-L1-Fc/huPD-1 binding)',
    'IC50 (huPD-L1-Fc/huB7.1-Fc binding)',
    'IC50 (MMAE ADC)',
    'IC50 (MMAF ADC)',
    'IC50 (Duo ADC)',
    'IC50 (oligomer)',
    'ELISA IC50 Dimer',
    'hIL6R/hIL6 IC50 (Binding Inhibition)',
    'XG-1 cell proliferation IC50 (Inhibition)',
    'HepG2/Stat3 Luciferase activity IC50',
    'IC50 (hIgG1)',
    'IC50 (IL-6 release assay)',
    'IC50 (IL-8 release assay)',
    'IC50 (cell death induction assay)',
    'apparent binding affinity (competition binding assay, IC50)',
    'IC50 (M-CSF Mouse Monocytic Cell Proliferation Assay)',
    'IC50 (pH 7.4)',
    'IC50 (pH 6.0)',
    'IC50 (chemotaxis, IgG1, rhIP-10 1 nM or 0.2 nM)',
    'IC50 (calcium flux, IgG1, rhIP-10 10 nM)',
    'IC50 (chemotaxis, IgG1, native hIP-10 0.6 nM)',
    'IC50 (chemotaxis)',
    'IC50 (calcium flux)',
    'Neut IC50 (μg/ml), subtype B',
    'IC50 (μg/ml), HMPV-A1',
    'Neut IC50 (μg/ml), subtype A',
    'IC50 (subtype A)',
    'IC50 (subtype B)',
    'Neut IC50 (subtype A)',
    'Neut IC50 (subtype B)',
    'Neut IC50 subtype B',
    'Neut IC50 subtype A',
    'Neut IC50 (μg/ml) subtype A',
    'Neut IC50 (μg/ml) subtype B',
    'IC50 (STAT6 Bioassay, IL-13)',
    'IC50 (TF1 Bioassay, IL-13)',
    'IC50 (PACAP38-induced PAC1-R mediated cAMP increase)',
    'IC50 (PACAP27-induced PAC1-R mediated cAMP increase)',
    'IC50 (PACAP38-induced cAMP increase in cells expressing human VPAC1-R)',
    'IC50 (PACAP38-induced cAMP increase in cells expressing human VPAC2-R)',
    'Calcium Flux IC50',
    'hIL6R/hIL6 Binding Inhibition IC50',
    'XG-1 cell proliferation Inhibition IC50',
    'IC50 (aggregometry, inhibition of platelet aggregation)',
    'IC50 (FACS, inhibition of fibrinogen binding)',
    'IC50 (CTLA4/B7.2 Comp. ELISA)',
    'IC50 (CTLA4/B7.1 Comp. ELISA)',
    'IC50 (Daudi cell proliferation)',
    'IC50 (U937 ISRE-RG reporter)',
    'LBB assay IC50',
    'IC50 (Daudi Cell Proliferation)',
    'IC50 (ISRE-RG Reporter, U937)',
    'IC50 (ID1, TAQMAN®)',
    'IC50 (pSmad1, Western)',
    'IC50 (HTRF Receptor Neutralisation)',
    'IC50 (Primary T-cell Assay)',
    'IC50 pseudotyped lenti neutralization',
    'Concentration for 50% inhibition (IC50)',
    'IC50 (M) (ELISA format 2, hGFRα3-mmH binding to hARTEMIN-mmH and hRET-10His)',
    'IC50 (nM) (Inhibition of ARTEMIN-dependent stimulation of HEK293/hGFRα3/hRET/SRE-luc cells)',
    'IC50 (nM) (Inhibition of ARTEMIN-dependent stimulation of HEK293/MfGFRα3/MfRET/SRE-luc cells)',
    'IC50 (M) (ELISA format 1, hGFRα3-hFc binding to hARTEMIN-mmH)',
    'IC50 (Proliferation of Human Primary NK Cells)',
    'IC50 (IFN-gamma production by Human NK Cells)',
    'IC50 (HT29 IL-8 release, HTRF)',
    'IC50 (HVEM, HTRF)',
    'IC50 (LTβR, HTRF)',
    'IC50 (FACS, PD-L1)',
    'IC50 (FMAT, PD-L1)',
    'IC50 (FMAT, PD-L2)',
    'IC50 (monomer)',
    'IC50 (ID1 TAQ-MAN®)',
    'IC50 (pSmad1 Western)',
    'IC50 (Fab-Fc fusion protein)',
    'IC50 (mAb)',
    'IC50 (bivalent target binding)',
    'IC50 (monovalent target binding)',
    'HGF/c-Met binding IC50',
    'Activity of inhibition of cell proliferation (MKN45) IC50',
    'IC50 (F.X activation)',
    'IC50 (F.IX activation)',
    'ELISA IC50',
    'IC50 (Neut, subtype A)',
    'IC50 (Neut, subtype B)',
    'Neut IC50 (μg/ml) A',
    'IC50 (RSV subtype A)',
    'IC50 (RSV subtype B)',
    'IC50 (ISRE Neutralization)',
    'IC50 (pSTAT1 Inhibition)',
    'IC50 ISRE Neutralization',
    'IC50 pSTAT1 inhibition',
    'IC50 (Inhibition on the proliferation of IL-4)',
    'IC50 (Inhibition on the proliferation of IL-13)',
    'IC50 (bivalent)',
    'IC50 (monovalent)',
    'IC50 (bivalent mAb)',
    'IC50 (Fab-Fc fusion, monovalent)',
    'IC50 (nM)',
    'Hemolytic assay IC50',
    'C3b IC50',
    'ELISA IC_50 Dimer',
    'IC_50',
    'TSLP concentration for 50% inhibition of TARC mRNA expression',
    'competitive ELISA (affinity)',
    'Affinity by competitive ELISA',
    'NOB (Neutralization of Binding) 50% concentration',
    'relative affinity (amount of competitor necessary for reducing binding of radioactive labelled Lewis b to H. pylori strain 17875/Leb to 50%)',
    'concentration for 50% plaque reduction (neutralization assay)',
    'concentration required to block CD32a-dependent platelet aggregation',
    'IC50 (RLB)',
    'IC50 (RGA)',
    'PD-L1 Competition, IC50',
    'Cytotoxicity IC50',
    'PD-L2 Competition, IC50'
    'IC50 (Classical Pathway)',
    'IC50 (Alternative Pathway)',
    'IC50 (MEK)',
    'IC50 (ERK)',
    'IC50 concentration',
    'Phage IC50',
    'IC50 for ligand depletion (molar ratio)',
    'IC50 ELISA',
    'IC50 (with pre-incubation)',
    'IC50 (without pre-incubation)',
    'blocking IC50',
    'IC50 (native, full-length substrate)',
    'IC50 FACS',
    'LPS Neut (O1) IC50',
    'SBA Kp4211lux IC50',
    'D Capsule OPK IC50',
    'Neutral. IC50',
    'IC50 (proMMP9)',
    'IC50 (CPM)',
    'IC50 (Gamma)'
    'IC50 (CPM, SEB assay)',
    'IC50 (IFN-γ, SEB assay)',
    'VLA1 Inhibition (IC50)',
    'α1I Inhibition (IC50)',
    'Competition with biotin-AQC2 (IC50)',
    'IC50 pSTAT1 Inhibition',
    'Amount of Ab required for 50% Inhibition',
    'apparent IC50',
    'RL-ELISA IC50',
    'TF-1 proliferation IC50',
    'IC50 IL-6',
    'IC50 IL-8',
    'Relative IC50',
    'Absolute IC50',
    'IC50-MFI',
    'PD-L2 Competition, IC50',
    'Plasma IC50',
    'IC50 (Classical Pathway)',
    'VNA IC50',
    'IC50 (Gamma)',
    'IC50 (CPM, SEB assay)',
    'IC50 (OPTS)',
    'IC50 (Wnt signaling)'
    'IC50 CSF-1R Phosphorylation',
    'IC50 (Wnt signaling)',
    'IC50 CSF-1R Phosphorylation',
    'IC50 for ligand depletion',
    'IC50 (Western)',
    'IC50 (TAQMAN®)',
]


measurement_map['EC50'] = [
    'EC50',
    'EC-50',
    'apparent affinity EC50',
    'Proliferation EC50',
    'luciferase activation, soluble IgG, EC_50',
    'SPR EC50',
    'EC50 (binding to hCD47 on CHO cells, IgG1 yeast)',
    'EC50 (binding to hCD47 on CHO cells, IgG4 CHO)',
    'EC50 (cytokines IFN-γ release)',
    'EC50 (TOK107-hIg, M)',
    'EC50 (Cells, M)',
    'amount to reach 50% of plateau (EC50 equivalent)',
    'EC50 (competitive ELISA)',
    'EC50 (blocking PDL-1/PD-1 interaction)',
    'EC50 (Denatured SOD1)',
    'EC50 (Oxidized SOD1)',
    'EC50 (Recombinant SOD1)',
    'EC50 (Native SOD1)',
    'EC50 RBA',
    'EC50 ELISA assay',
    'EC50 ICAM1 cell RBA (CHO-CD40)',
    'Luciferase assay (EC50)',
    'MLR assay (EC50)',
    'EC50 (Luciferase assay)',
    'EC50 (MLR assay)',
    'CD40 Binding ELISA EC50',
    'Flow EC50',
    'EC50 (Daudi cell proliferation, IFN alpha 2b)',
    'EC50 (ISRE-RG Reporter, U937, IFN alpha 2b)',
    'EC50 (Daudi cell proliferation, IFN omega)',
    'half-maximal binding (EC50)',
    'EC50 (ELISA, CD74v1)',
    'EC50 (ELISA, CD74v2)',
    'EC50 (FACS, cellular CD74 on Raji cells)',
    'EC50 (FACS, surface CD74 on Daudi cells, unconjugated)',
    'EC50 (FACS, surface CD74 on Daudi cells, vcMMAE conjugate)',
    'EC50 (FACS, surface CD74 on Daudi cells, mcMMAF conjugate)',
    'EC50 (cell killing, anti-kappa-ETA′ pre-incubated, Raji cells)',
    'EC50 (50% Bmax)',
    'ELISA EC50',
    'EC50 to peptide',
    'EC50 to denatured protein',
    'EC50 (ELISA)',
    'EC50 (CELISA)',
    'EC50 (human neutrophils)',
    'EC50 (L1.2/hC5aR transfectants)',
    'MAC Deposition EC50',
    'EC50 proliferation',
    'EC50 IFNγ production',
    'Half-max binding (EC50)',
    'EC50 (FXa)',
    'EC50 (FXa-FVIIa)',
    'EC50 (IFN-γ inhibition)',
    'EC50 (TNF-α inhibition)',
    'Affinity by ELISA',
    'EC50 (with GARP)',
    'IFNγ EC50',
    'EC50 w/plasma',
    'EC50 w/o plasma',
    'protein binding activity EC50',
    'cell binding activity EC50',
    'EC50 (FACS)',
    'EC50 Without Cross-linker',
    'EC50 With Cross-linker'
    'EC50 (IFNγ)',
    'EC50 (Proliferation of T cells)',
    'ADC EC50',
    'EC50 for cytokines IFN-γ release',
    'ADCC EC50',
    'CAGA EC50',
    'EC50 molar ratio for ligand depletion (DAKD)',
    'EC50 molar ratio for ligand depletion (DAKLP)',
    'EC50 FACS JURKAT',
    'EC50 hPBMC Proliferation',
    'EC50 Bead RBA',
    'EC50 ELISA',
    'EC50 binding Calu6'
    'EC50 enz. inhibition Calu6',
    'EC50 Calu6 inhibition',
    'EC50 SKMEL24 inhibition',
    'EC50 H292 inhibition',
    'apparent EC50',
    'EC50 IgG',
    'EC50 TCB',
    'FACS EC50',
    'FACS (EC50)',
    'EC50 CHO-Tim3',
    'pSyk EC50',
    'ELISA (EC50)',
    'EC50 fibrillary Tau pS422',
    'Cell Binding EC50',
    'FACS binding EC50',
    'AMFI EC50',
    'EC50 at pH 7.4',
    'EC50 at pH 6.0',
    'apparent affinity EC50',
    'EC50 (tumor cell killing, 24 h)',
    'EC50 (tumor cell killing, 48 h)',
    'EC50 (CD4+ CD69+)',
    'EC50 (CD4+ CD25+)',
    'EC50 (CD8+ CD69+)',
    'EC50 (CD8+ CD25+)',
    'TCF EC50',
    'ST2 EC50',
    'EC50 With Cross-linker',
    'EC50 (IFNγ)',
    'EC50 binding Calu6',
    'EC50 enz. inhibition Calu6',
    'ΔMFI_ EC50',
    'Direct ELISA EC50',
    'ICA EC50',
    '~EC50 Kd'
]

measurement_map['GI50'] = [
    '50% minimum growth inhibitory concentration'
]
measurement_map['ED50'] = [
    'ED50',
    'ED50 (ELISA rhIL-13Rα2)',
    'ED50 (cELISA A375 cells)',
]

# standard_unit: 1/Ms
measurement_map['kon'] = [
    'kon',
    'k_on',
    'Kon',
    'KON',
    'K_on',
    'apparent kon',

    'Fab kon',
    'kon (BIAcore)',
    'kon (ForteBio)',
    'k_on (CaCl2, Biacore)',
    'k_on (MgCl2, Biacore)',
    'kon (CaCl2)',
    'kon (MgCl2)',
    'k_on (CaCl2)',
    'k_on (MgCl2)',
    'apparent association rate (K_ON)',
    'FACS kon',

    'On-rate',
    'on-rate',
    'High affinity binding site kon',
    'Low affinity binding site kon',
]

# standard unit: 1/s
measurement_map['koff'] = [
    'koff',
    'Koff',
    'k_off',
    'k_off',
    'K_off',
    'KOFF',
    'koff (BIAcore)',
    'koff (ForteBio)',
    'apparent koff',
    'dissociation rate constant (k_off)',

    'koff (CaCl2)',
    'koff (MgCl2)',
    'k_off (CaCl2)',
    'k_off (MgCl2)',
    'k_off (CaCl2, Biacore)',
    'k_off (MgCl2, Biacore)',

    'off rate',
    'off-rate',
    'Off-rate',
    'SPR Koff at pH 6.0',
    'SPR Koff at pH 7.4',
    'apparent dissociation rate (K_OFF)',
    'High affinity binding site koff',
    'Low affinity binding site koff',

    'koff 7.4 >> 5.8',
    'Fab koff',
    'FACS koff',
]

# standard unit: s
measurement_map['t½'] = [
    't½',
    't ½',
    'T½',
    't1/2',
    't_1/2',
    'T1/2',
    'T 1/2',
    't½ (pH 7.4)',
    't½ (pH 5.0)',
    't½ (min) (pH 7.4)',
    't½ (min) (pH 5.0)',

    'T1/2 dimeric',
    'T1/2 monomeric',
    't/2 diss',
    't/2-diss',
    't1/2 diss',
    't/2diss (early, 10 s)',
    't/2diss (late, 50 s)',
    'off-rate (half-life)',
]
# standard unit: 1/Ms
measurement_map['ka'] = [
    'ka',
    'k_a',
    'ka, app',
    'BIACORE ka',
    'BIACORE™ ka',

    'ka (25°C)',
    'ka (37°C)',
    'ka (pH 7.4)',
    'ka (pH 5.8)',
    'ka (1/Ms) (pH 7.4)',
    'ka (1/Ms) (pH 6.0)',

    'ka (PACAP38)',
    'ka (PACAP27)',
    'ka (hIgG1)',
    'ka (huPD-L1-his)',
    'ka (CynoPD-L1-his)',

    'ka @ 25°C (34mer)',
    'ka @ 37°C (34mer)',
    'ka @ 37°C (84mer)',
    'ka @ 25° C. - 34mer',
    'ka @ 37° C. - 34mer',
    'ka @ 37° C. - 84mer',

    'kassoc',
    ]

# standard unit: 1/M
measurement_map['Ka'] = [
    'Ka',
    'K_a',
    'KA',
    'K_A',

    'kass',
    'Kass',
    'Biacore Ka',
    'association constant',
    'binding constant (Ka)',
    'affinity constant (Ka)',
    'Ka (relative affinity constant)',
    'equilibrium association constant',
    'apparent association rate constant (K_a)',
    'binding affinity (reciprocal of antigen concentration at 50% inhibition, as per Friguet method)',
    'Ka (Biacore)',
]

measurement_map['Ki'] = [
    'Ki',
    'KI',
    'Kiapp',
    'Ki_app',
    'Ki,app',
    'apparent Ki',
    'Ki (pseudo-Cath-D)',
    'Ki (mature Cath-D)',
]

# standard unit: °C, K
measurement_map['Tm'] = [
    'Tm',
    'TM'
]
measurement_map['ΔG'] = [
    'ΔG'
]
measurement_map['Rmax'] = [
    'Rmax',
]

unit_map = {}

unit_map['IC50'] = {
    # Concentration units → normalize to nM
    'pM':       ('nM',  1e-3),
    'pm':       ('nM',  1e-3),
    'ρM':       ('nM',  1e-3),   # typo
    'nM':       ('nM',  1),
    'nm':       ('nm',  1),      # typo
    'nmol/L':   ('nM',  1),
    'uM':       ('nM',  1e3),
    'μM':       ('nM',  1e3),
    'microM':   ('nM',  1e3),
    'mM':       ('nM',  1e6),
    'M':        ('nM',  1e9),
    'molar':    ('nM',  1e9),

    # Mass-per-volume units → normalize to μg/mL
    'pg/mL':        ('μg/mL',   1e-6),
    'pg/ml':        ('μg/mL',   1e-6),
    'ng/ml':        ('μg/mL',   1e-3),
    'ng/mL':        ('μg/mL',   1e-3),
    'ng Ab/mL':     ('μg/mL',   1e-3),
    'ng/nL':        ('μg/mL',   1e-3),    # check -> typo
    'µg/ml':        ('μg/mL',   1),
    'ug/ml':        ('μg/mL',   1),
    'ug/mL':        ('μg/mL',   1),
    'μg/ml':        ('μg/mL',   1),
    'μg/mL':        ('μg/mL',   1),
    'µg/mL':        ('μg/mL',   1),
    'microgr/mL':   ('μg/mL',   1),
    'microgr/ml':   ('μg/mL',   1),
    'mg/ml':        ('μg/mL',   1e3),
    'mg/mL':        ('μg/mL',   1e3),
    'g/ml':         ('μg/mL',   1e6),

    # inappropriate units
    # 'pmoles/mouse': ('pmole', 1),
    # '1/M': ('1/nM', 1e9),
    # 'μg/test': ('μg/test', 1),
    # 'relative to G6.31': ('relative to G6.31', 1)
    # 'μg/well': ('μg/well', 1)
}

unit_map['EC50'] = {
    # Concentration units → normalize to nM
    'pM':       ('nM',  1e-3),
    'pm':       ('nM',  1e-3),
    'pm':       ('nM',  1e-3),
    'nM':       ('nM',  1),
    'nmol/L':   ('nM',  1),
    'nMol/L':   ('nM',  1),
    'μM':       ('nM',  1e3),
    'microM':   ('nM',  1e3),
    'M':        ('nM',  1e9),

    # Mass-per-volume units → normalize to μg/mL
    'pg/ml':    ('μg/mL', 1e-6),
    'pg/mL':    ('μg/mL', 1e-6),
    'ng/ml':    ('μg/mL', 1e-3),
    'ng/mL':    ('μg/mL', 1e-3),
    'µg/ml':    ('μg/mL', 1),
    'ug/ml':    ('μg/mL', 1),
    'ug/mL':    ('μg/mL', 1),
    'μg/ml':    ('μg/mL', 1),
    'μg/mL':    ('μg/mL', 1),
    'µg/mL':    ('μg/mL', 1),
    'mg/ml':    ('μg/mL', 1e3),
    'g/mL':     ('μg/mL', 1e6),

    # Pure mass units -> inappropriate
    # 'ng':       ('ng',     1),
    # 'μg':       ('μg',     1),
    # 'μg/test':  ('μg/test',1),
    # 'ng/well'
    # 'pmoles/mouse': ('nM',     1e-3),
    # 'cells'
    # 'log'
    # 'mg/kg'
    # 'null'
    # '°C'
}

unit_map['KD'] = {
    # Concentration units → normalize to nM
    'fM':           ('nM', 1e-6),
    'pM':           ('nM', 1e-3),
    'ρM':           ('nM', 1e-3),   # typo
    'pmol/L':       ('nM', 1e-3),
    'picomolar':    ('nM', 1e-3),
    '1e-12 M':      ('nM', 1e-3),
    '×10^−12 M':    ('nM', 1e-3),
    'M ×10^-12':    ('nM', 1e-3),

    '10^-11 M':     ('nM', 1e-2),
    '1E-10 M':      ('nM', 1e-1),
    '10^−10 M':     ('nM', 1e-1),
    '×10^-10 M':    ('nM', 1e-1),
    'x10^-10 M':    ('nM', 1e-1),
    '10^-10 M':     ('nM', 1e-1),
    'M × 10^-10':   ('nM', 1e-1),

    '×10−9 M':      ('nM', 1),
    '10^-9 M':      ('nM', 1),
    '10^(-9)M':     ('nM', 1),
    '10^-9 mol/L':  ('nM', 1),
    '×10^−9 M':     ('nM', 1),
    '1E-9 M':       ('nM', 1),

    '1E-09M':       ('nM', 1),
    'nM':           ('nM', 1),
    'nmol/L':       ('nM', 1),
    'nmol/l':       ('nM', 1),     # typo
    'nanomolar':    ('nM', 1),
    'nanomoles/liter':('nM', 1),
    'nm':           ('nM', 1),     # typo
    'μM':           ('nM', 1e3),
    'µM':           ('nM', 1e3),
    'uM':           ('nM', 1e3),
    'M':            ('nM', 1e9),
    'Molar':        ('nM', 1e9),
    'mol/L':        ('nM', 1e9),

    # Mass-per-volume units → normalize to μg/mL
    'μg/ml':        ('μg/mL', 1),
    'μg/mL':        ('μg/mL', 1),
    'ug/mL':        ('μg/mL', 1),
    'ug/ml':        ('μg/mL', 1),
    'µg/mL':        ('μg/mL', 1),
    'ng/ml':        ('μg/mL', 1e-3),
    'ng/mL':        ('μg/mL', 1e-3)

    # Inappropriate
    # '1/M':  ('1/nM', 1e-9),
    # 'nM^-1': ('nM^-1', 1),
    # 'E−09': ('E−09', 1),
    # '%': ('%', 1)
    # 'L/mol'
    # 'M^-1'
}

unit_map['Ka'] = {
    '1/M':          ('1/M', 1),
    'M−1':          ('1/M', 1),
    'M^-1':         ('1/M', 1),
    '(mol/L)^-1':   ('1/M', 1),

    'L/mol':        ('1/M', 1),
    'liters/mole':  ('1/M', 1),
    '10^10 L/mol':  ('1/M', 1e10),
    '1/M × 10^10':  ('1/M', 1e10),
    '10^10 1/M':    ('1/M', 1e10),
}

# standard_unit: 1/(M·s)
unit_map['ka'] = {
    'M−1s−1':       ('1/(M·s)', 1),
    'M-1s-1':       ('1/(M·s)', 1),
    'M−1·s−1':      ('1/(M·s)', 1),
    'M−1 s−1':      ('1/(M·s)', 1),
    'M-1 s-1':      ('1/(M·s)', 1),
    'M−1 S−1':      ('1/(M·s)', 1),
    'M^-1 s^-1':    ('1/(M·s)', 1),
    'M^−1 s^−1':    ('1/(M·s)', 1),
    'M^−1·s^−1':    ('1/(M·s)', 1),
    'M^-1 S^-1':    ('1/(M·s)', 1),
    'M^-1·c^-1':    ('1/(M·s)', 1),  # typo
    'M(−1) s(−1)':  ('1/(M·s)', 1),
    'M^-1s^-1':     ('1/(M·s)', 1),
    'M−1 · s−1':    ('1/(M·s)', 1),

    'M⁻¹ s⁻¹':      ('1/(M·s)', 1),
    'M⁻¹s⁻¹':       ('1/(M·s)', 1),
    'M⁻¹·s⁻¹':      ('1/(M·s)', 1),
    'M−1 * s−1':    ('1/(M·s)', 1),

    'M−1 sec−1':    ('1/(M·s)', 1),
    'M-1 sec-1':    ('1/(M·s)', 1),
    'M-1 Sec-1':    ('1/(M·s)', 1),
    'M-1 Sec-1':    ('1/(M·s)', 1),
    'M−1 Sec−1':    ('1/(M·s)', 1),
    'M^-1 sec^-1':  ('1/(M·s)', 1),

    'M^{-1} s^{-1}':('1/(M·s)', 1),
    'M^-1·s^-1':    ('1/(M·s)', 1),
    'M^-1*s^-1':    ('1/(M·s)', 1),
    'Ms−1':         ('1/(M·s)', 1),
    'M-1S-1':       ('1/(M·s)', 1),

    '1/Ms':         ('1/(M·s)', 1),
    '1/MS':         ('1/(M·s)', 1),
    'l/Ms':         ('1/(M·s)', 1),  # typo
    'l/mol * s':    ('1/(M·s)', 1),  # typo
    'l/mol*s':      ('1/(M·s)', 1),  # typo
    '1/M s':        ('1/(M·s)', 1),
    '1/M-s':        ('1/(M·s)', 1),
    '1/M.Sec':      ('1/(M·s)', 1),
    '1/M*s':        ('1/(M·s)', 1),
    '1/(Ms)':       ('1/(M·s)', 1),
    '1/(M*s)':      ('1/(M·s)', 1),
    '1/(M·s)':      ('1/(M·s)', 1),

    '1/M · s':      ('1/(M·s)', 1),
    '1/(M · s)':    ('1/(M·s)', 1),

    '(mol/L-s)^-1': ('1/(M·s)', 1),


    '10^-5 M^-1 s^-1':  ('1/(M·s)', 1e-5),

    '1e4 sec−1* M−1':   ('1/(M·s)', 1e4),
    'M−1 S−1/10^4':     ('1/(M·s)', 1e4),

    '×10^4 (1/M/s)':    ('1/(M·s)', 1e4),
    '10^4 M^-1 s^-1':   ('1/(M·s)', 1e4),
    '1/Ms * 10^4':      ('1/(M·s)', 1e4),

    '1e5 M−1 s−1':      ('1/(M·s)', 1e5),
    '10^5 M^-1 s^-1':   ('1/(M·s)', 1e5),
    '1/M × s × 10^5':   ('1/(M·s)', 1e5),

    '10^6/Ms':          ('1/(M·s)', 1e6),
    '10^6 M−1 S−1':     ('1/(M·s)', 1e6),
    '1/Ms ×10^6':       ('1/(M·s)', 1e6),
    'x10^6 M^-1 s^-1':  ('1/(M·s)', 1e6),
    'M^-1 S^-1 × 10^6': ('1/(M·s)', 1e6),
    'M^-1 s^-1 × 10^6': ('1/(M·s)', 1e6),
    'M^-1 s^-1 × 10^6': ('1/(M·s)', 1e6),
    'M^-1 S^-1 × 10^6': ('1/(M·s)', 1e6),
    '×10^6 M⁻¹ s⁻¹':    ('1/(M·s)', 1e6),
    '×10^6 M−1 s−1':    ('1/(M·s)', 1e6),

    '1e9 M^-1 s^-1':    ('1/(M·s)', 1e9),

    # Not allowed
    # 'M': ('M', 1)
    # 'M/s'
}

unit_map['kd'] = {
    '×10^-4 (1/s)': ('1/s', 1e-4),

    '1/s':          ('1/s', 1),
    'sec^-1':       ('1/s', 1),
    '1/s':          ('1/s', 1),

    's(−1)':        ('1/s', 1),
    's^-1':         ('1/s', 1),
    's−1':          ('1/s', 1),
    's-1':          ('1/s', 1),
    'S−1':          ('1/s', 1),
    'sec-1':        ('1/s', 1),
    '1/Sec':        ('1/s', 1),
    'S^-1':         ('1/s', 1),
    's^−1':         ('1/s', 1),
    's⁻¹':          ('1/s', 1),

    'l/s':          ('1/s', 1),
    's^{-1}':       ('1/s', 1),
    '1/S':          ('1/s', 1),
    'S-1':          ('1/s', 1),
    'sec−1':        ('1/s', 1),

    '1e-3 s−1':     ('1/s', 1e-3),
    '×10−3 sec−1':  ('1/s', 1e-3),
    's^-1 × 10^-4': ('1/s', 1e-4),
    '1/s (×10^−4)': ('1/s', 1e-4),
    '1/s × 10^−4':  ('1/s', 1e-4),
    '1/s ×10^-4':   ('1/s', 1e-4),
    '10^-4 s^-1':   ('1/s', 1e-4),
    '10^−4 S−1':    ('1/s', 1e-4),
    'S−1 × 10^−4':  ('1/s', 1e-4),
    'S^-1 × 10^-4': ('1/s', 1e-4),
    '10^-5/s':      ('1/s', 1e-5),
    '1e-5 sec−1':   ('1/s', 1e-5),
    '10^-5 sec^-1': ('1/s', 1e-5),
    '1e-10 s^-1':   ('1/s', 1e-10),
}

unit_map['kon'] = {
    '1/(M s)':      ('1/(M·s)', 1),
    '1/(mol·s)':    ('1/(M·s)', 1),
    '1/M/s':        ('1/(M·s)', 1),

    '1/Ms':         ('1/(M·s)', 1),
    '1/MS':         ('1/(M·s)', 1),
    'l/Ms':         ('1/(M·s)', 1),  # typo
    '1/M·s':        ('1/(M·s)', 1),
    '1/M*s':        ('1/(M·s)', 1),

    '1/M s':        ('1/(M·s)', 1),
    '1/(M·s)':      ('1/(M·s)', 1),
    '1/(Ms)':       ('1/(M·s)', 1),
    '1/(M*s)':      ('1/(M·s)', 1),
    '1/M.Sec':      ('1/(M·s)', 1),

    'M^−1·s^−1':    ('1/(M·s)', 1),
    'M^-1s^-1':     ('1/(M·s)', 1),
    'M^-1 s^-1':    ('1/(M·s)', 1),
    'M^-1·c^-1':    ('1/(M·s)', 1),  # typo
    'M−1·s−1':      ('1/(M·s)', 1),
    'M-1 · s-1':    ('1/(M·s)', 1),
    'M−1×S−1':      ('1/(M·s)', 1),
    'M−1 sec−1':    ('1/(M·s)', 1),
    'M-1 Sec-1':    ('1/(M·s)', 1),
    'M−1 Sec−1':    ('1/(M·s)', 1),
    'M−1·sec−1':    ('1/(M·s)', 1),
    'M−1 × S−1':    ('1/(M·s)', 1),
    'M^-1 sec^-1':  ('1/(M·s)', 1),
    'M^−1 sec^−1':  ('1/(M·s)', 1),
    'M^−1·sec^−1':  ('1/(M·s)', 1),
    'M^-1·sec^-1':  ('1/(M·s)', 1),

    'Ms⁻¹':         ('1/(M·s)', 1),
    'Ms−1':         ('1/(M·s)', 1),
    'M−1s−1':       ('1/(M·s)', 1),
    'M-1s-1':       ('1/(M·s)', 1),
    'M-1S-1':       ('1/(M·s)', 1),
    'M−1 s−1':      ('1/(M·s)', 1),
    'M−1 S−1':      ('1/(M·s)', 1),
    'M-1 s-1':      ('1/(M·s)', 1),
    'M^−1 s^−1':    ('1/(M·s)', 1),
    'M^−1 S^−1':    ('1/(M·s)', 1),
    'M^-1.S^-1':    ('1/(M·s)', 1),
    'M^-1 S^-1':    ('1/(M·s)', 1),
    'M^-1·s^-1':    ('1/(M·s)', 1),
    'M^{-1} s^{-1}':('1/(M·s)', 1),
    'l mol−1 s−1':  ('1/(M·s)', 1),

    's−1 M−1':      ('1/(M·s)', 1),

    '×10^4 1/Ms':       ('1/(M·s)', 1e4),
    'M−1 S−1/10^4':     ('1/(M·s)', 1e4),
    '1e4 M^-1 s^-1':    ('1/(M·s)', 1e4),
    'M^−1 s^−1 /10^4':  ('1/(M·s)', 1e4),
    '×10^4 (1/M/s)':    ('1/(M·s)', 1e4),
    'M^-1 s^-1 × 10^4': ('1/(M·s)', 1e4),

    '1/Ms × 10^5':      ('1/(M·s)', 1e5),
    '×10^5 1/MS':       ('1/(M·s)', 1e5),
    'xE+5/Ms':          ('1/(M·s)', 1e5),
    '10^5/Ms':          ('1/(M·s)', 1e5),
    '10^5 1/Ms':        ('1/(M·s)', 1e5),
    '10^5 mol/L/s':     ('1/(M·s)', 1e5),
    '10^5 mol/Ls':      ('1/(M·s)', 1e5),  # source-specific malformed notation
    '10^5 M^-1 s^-1':   ('1/(M·s)', 1e5),
    '10^5 M^−1 s^−1':   ('1/(M·s)', 1e5),
    '10^5 (M^−1 s^−1)': ('1/(M·s)', 1e5),
    '1/M × s × 10^5':   ('1/(M·s)', 1e5),
    '× 10^5 M^−1 sec^−1':('1/(M·s)', 1e5),
    '1e5 M^-1 s^-1':    ('1/(M·s)', 1e5),

    '×10^6 1/Ms':       ('1/(M·s)', 1e6),
    '×10^6 M−1 s−1':     ('1/(M·s)', 1e6),
    '10^6 M−1s−1':      ('1/(M·s)', 1e6),
    '10^6 M^-1 s^-1':   ('1/(M·s)', 1e6),
    '×10^6 M^-1 s^-1':  ('1/(M·s)', 1e6),
    'x10^6 M^-1 s^-1':  ('1/(M·s)', 1e6),

    'nM-1day-1':        ('1/(M·s)', 1e9/86400),
    'nM−1day−1':        ('1/(M·s)', 1e9/86400),
    'nM^-1 day^-1':     ('1/(M·s)', 1e9/86400),

    # Not allowed
    # '1/s'
}

unit_map['koff'] = {
    '1/s':          ('1/s', 1),
    '1/S':          ('1/s', 1),
    '1/sec':        ('1/s', 1),
    '1/s (10E−4), pH 5.5': ('1/s', 1e-4),
    '1/s (10E−4), pH 7.4': ('1/s', 1e-4),

    's⁻¹':          ('1/s', 1),
    's-1':          ('1/s', 1),
    's−1':          ('1/s', 1),
    'S−1':          ('1/s', 1),
    's^−1':         ('1/s', 1),
    's^-1':         ('1/s', 1),
    'S^−1':         ('1/s', 1),
    'S^-1':         ('1/s', 1),

    'sec−1':        ('1/s', 1),
    'sec^−1':       ('1/s', 1),
    'sec^-1':       ('1/s', 1),

    '×10−3/s':      ('1/s', 1e-3),
    '1e-3 s^-1':    ('1/s', 1e-3),
    'xE−3/s':       ('1/s', 1e-3),
    '×10^−3 1/s':   ('1/s', 1e-3),
    '×10^-3 sec^-1':('1/s', 1e-3),


    '10^-4/s':      ('1/s', 1e-4),
    '10^-4 1/s':    ('1/s', 1e-4),
    '10^3 s^-1':    ('1/s', 1e-3),
    '10^4 S−1':     ('1/s', 1e-4),
    '10^4 s^−1':    ('1/s', 1e-4),
    '10^4 s^-1':    ('1/s', 1e-4),
    '10^(-4) s-1':  ('1/s', 1e-4),
    '10^-4s-1':     ('1/s', 1e-4),
    '10^-4 s^-1':   ('1/s', 1e-4),
    '10^−4 s^−1':   ('1/s', 1e-4),
    's^-1 x 10^-4': ('1/s', 1e-4),
    's^-1 × 10^-4': ('1/s', 1e-4),
    '10^−4 (s^−1)': ('1/s', 1e-4),


    '1e-4 s^-1':    ('1/s', 1e-4),
    '1e-4 sec^-1':  ('1/s', 1e-4),
    '×10^−4 1/s':   ('1/s', 1e-4),
    '×10^-4 s^-1':  ('1/s', 1e-4),
    'x10^-4 s^-1':  ('1/s', 1e-4),
    '×10^-4 s^-1':  ('1/s', 1e-4),
    '× 10^−4 sec^−1':('1/s', 1e-4),
    '× 10⁻⁴ sec⁻¹': ('1/s', 1e-4),

    '10^-5/s':      ('1/s', 1e-5),
    '10^-5 s^-1':   ('1/s', 1e-5),
    '×10^−5 1/s':   ('1/s', 1e-5),
    '1/s × 10^-5':  ('1/s', 1e-5),
    '×10^−6 sec−1': ('1/s', 1e-6),

    'min⁻¹':        ('1/s', 1/60),
    'day-1':        ('1/s', 1/86400),
    'day^-1':       ('1/s', 1/86400),
    'day−1':        ('1/s', 1/86400),

    # Not allowed
    # 'M−1'
    # 's'
}

unit_map['ED50'] = {
    # Concentration units → normalize to nM
    'nM': ('nM', 1),
    'nmol/L': ('nM', 1),
    'uM': ('nM', 1e3),

    # Mass-per-volume units → normalize to μg/mL
    'ng/ml': ('μg/mL', 1e-3),
    'ng/mL': ('μg/mL', 1e-3),
    'μg/mL': ('μg/mL', 1),
    'μg/ml': ('μg/mL', 1)
}

unit_map['GI50'] = {
    'ng/mL':    ('μg/mL', 1e-3)
}

unit_map['t½'] = {
    's':        ('s', 1),
    'sec':      ('s', 1),
    'seconds':  ('s', 1),

    'min':      ('s', 60),
    'm':        ('s', 60),

    'h':        ('s', 60*60),
    'hr':       ('s', 60*60),
    'hour':     ('s', 60*60),

    'day':      ('s', 60*60*24),
    'days':     ('s', 60*60*24)
}

unit_map['Ki'] = {
    'pM':   ('nM', 1e-3),
    'nM':   ('nM', 1)
}

unit_map['Tm'] = {
    '°C':       ('°C', 1),
    'Celcius':  ('°C', 1),
    'K':    ('K', 1)
}

unit_map['Rmax'] = {
    'RU': ('RU', 1),
}

def get_measurement_map():
    return measurement_map

def get_unit_map():
    return unit_map

class StandarizeValue:
    def __init__(self):

        self.unit_map = unit_map
        self.measurement_map = measurement_map
        measurment2std = {}
        for std_key, raws in measurement_map.items():
            for raw in raws:
                measurment2std[raw] = std_key
        self.measurement2std = measurment2std


    def correct_measurement_and_unit(self, raw_meas: str, raw_unit: str, raw_value):
        """
        raw_meas: 처음 매핑된 standard_measurement (Ka, ka, Kd, kd 중 하나)
        raw_unit: 실제 들어온 단위 문자열 (예: "nM", "1/s", "M^-1", ...)
        raw_value: 원값 (숫자)

        반환: (correct_meas, std_unit, std_value) 또는 (None, None, None) if no match
        """
        std_meas = self.measurement2std.get(raw_meas, 'etc')
        if isinstance(raw_value, str):
            raw_value = str(raw_value).replace('−', '-')
            raw_value = float(raw_value)

        # 2) 네 가지 지표만 처리
        if std_meas == 'etc':
            return std_meas, raw_unit, raw_value

        if std_meas not in ("Ka", "ka", "Kd", "kd", "KD"):
            cmap = unit_map.get(std_meas, {})
            std_unit, factor = cmap.get(raw_unit, (None, None))
            if std_unit:
                std_value = float(raw_value) * factor
            else:
                std_value = None
            return std_meas, std_unit, std_value  # correction 대상 아님

        # 3) 어느 unit_map에 속하는지 검사
        else:
            for corr_meas in ("Ka", "ka", "Kd", "kd", "KD"):
                cmap = unit_map.get(corr_meas, {})
                if raw_unit in cmap:
                    std_unit, factor = cmap.get(raw_unit, (None, None))
                    std_value = float(raw_value) * factor

                    return corr_meas, std_unit, std_value

        # 4) 어디에도 속하지 않으면
        return None, None, None


    def convert(self, row):
        meas = row['measurement']
        unit = row['unit']
        value = row['value']

        corr_meas, std_unit, std_value = self.correct_measurement_and_unit(meas, unit, value)

        return pd.Series([corr_meas, std_value, std_unit])


    def standarize(self, df,
                   measurement_col='measurement', out_measurement_col='standard_measurement',
                   value_col='value', out_value_col='standard_value',
                   unit_col='unit',out_unit_col='standard_unit'):
        """
        :param df: DataFrame with value, unit, and type columns
        :return: df with additional standardized value/unit columns
        """

        df[[out_measurement_col, out_value_col, out_unit_col]] = df.apply(self.convert, axis=1)
        return df