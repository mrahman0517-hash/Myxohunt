# Sources

Every fact we use in the project, with a link and one or two sentences on what we took from it.
Links were checked on 9 October 2026. "Checked from abstract" means I read the abstract or a
summary, not the full paper. Add new entries here whenever a new fact enters the model.

## The main paper and its code

**Saulnier et al. 2026, *Nature Physics* — Mechanisms of spatial pattern transition in motile bacterial collectives.**
[doi:10.1038/s41567-026-03416-y](https://doi.org/10.1038/s41567-026-03416-y) · PDF in `Resources/`
- The base of the whole model. One frustration-driven reversal rule makes both patterns; the
  only difference is alignment (slime trails off prey, one shared axis on prey matrix).
- Supplies every Myxo body and motion number: 10 discs, 5 µm long, 0.7 µm wide, 4 µm/min.
  Ripples form on prey once it has been fully digested.
- Re-read 11 Oct 2026 (local PDF):
  - A Myxo colony "invades and digests" an E. coli colony "within 48 h" (Fig. 1a).
  - Rippling waves "form inside the prey colony once the prey has been entirely digested"
    (Fig. 1b), "following prey consumption and the onset of starvation". This counts against
    B76's living-prey trigger.
  - In their simulations cells stay about twice as long in rippling fields as in swarming fields
    (Fig. 6c). In experiments, non-reversing mutants are sorted out of the rippling field
    (Fig. 6e): rippling holds a pack in place through reversals.
  - Fruiting-body formation is delayed where prey is present (their ref. 64).

**Authors' code and data.**
[github.com/MignotLab/SpatialPatternsCollectives](https://github.com/MignotLab/SpatialPatternsCollectives) ·
[Figshare data, doi:10.6084/m9.figshare.30667151](https://doi.org/10.6084/m9.figshare.30667151)
- Fills gaps the PDF leaves to its Supplement: the reversal curves, the EPS grid mechanics, the
  step order. Details are in `docs/model-foundations.md`.

## Rippling and predation

**Shimkets & Kaiser 1982, *J. Bacteriol.* 152:451 — Induction of coordinated movement of *M. xanthus* cells.**
[doi:10.1128/jb.152.1.451-461.1982](https://doi.org/10.1128/jb.152.1.451-461.1982) · checked from abstract
- Prey cell-wall material (murein, i.e. peptidoglycan) from many bacteria makes resting Myxo
  cells ripple. This is why our ripple trigger is "prey matrix on the ground".

**Berleman et al. 2006, *J. Bacteriol.* 188:5888 — Rippling is a predatory behavior in *M. xanthus*.**
[doi:10.1128/JB.00559-06](https://doi.org/10.1128/JB.00559-06) · checked from the abstract (via Europe PMC, PMC1540073)
- Rippling appears during predation and is triggered by prey or other large molecules, not
  specifically by the C-signal. Rippling helps predation. Supports allowing ripples on
  partly eaten prey.
- The abstract says rippling occurs when cells "make direct contact with either prey or large
  macromolecules" (peptidoglycan, protein, nucleic acid). It doesn't occur with the small
  building blocks, nor when the macromolecules are kept apart from the cells. So contact with
  living prey counts too (B76).

**Berleman et al. 2008, *PNAS* 105:17127 — Predataxis behavior in *M. xanthus*.**
[doi:10.1073/pnas.0804387105](https://doi.org/10.1073/pnas.0804387105) · checked from abstract
- Cells show directed, chemotaxis-like movement toward prey during predatory rippling. This is
  the basis for an optional "weak pull toward prey".
- **Correction (11 Oct 2026, abstract re-read via Europe PMC):** the abstract says ripple
  wavelength is "adaptable and dependent on prey cell availability" but not which way it changes.
  An earlier note here said "shrinks with more prey", which isn't in the abstract.
- Frz mutants "are defective in directing cell movement through prey colonies": the Frz
  reversal system steers cells through prey.

**Zhang et al. 2012, *PLoS Comput. Biol.* 8:e1002715 — Mechanistic basis of *M. xanthus* rippling and its role during predation.**
[doi:10.1371/journal.pcbi.1002715](https://doi.org/10.1371/journal.pcbi.1002715) · checked from abstract
- An earlier rippling model, cited by our paper. Its biological conclusion: rippling helps
  cells spread over prey faster and stay on prey longer.
- Its model needs side-to-side signalling that triggers reversals, a short refractory period
  and alignment. It proposes that prey macromolecules start ripples by stimulating that
  signalling (abstract, re-read 11 Oct 2026). We tested a version of this ("prey shorten the
  lock-out") and it didn't keep more cells at the prey (B77).

**Rombouts et al. 2023, *Nat. Commun.* 14:5588 — Multi-scale dynamic imaging reveals that cooperative motility behaviors promote efficient predation in bacteria.**
[doi:10.1038/s41467-023-41193-x](https://doi.org/10.1038/s41467-023-41193-x) ·
[PMC10495355](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10495355/) · checked from abstract
- From the Mignot lab, and the main paper's ref. 7. Whole predatory communities were tracked
  at single-cell resolution.
- Lone foragers and swarms both contain A- and S-motile cells, and single cells switch often
  between foragers and swarms.
- A-motility is critical for directional movement of both, and A- and S-motile cells together
  make predation more efficient.
- Basis for scouts (decision-log B67), with scouting as a behaviour rather than a fixed type.
- Full text (via Europe PMC, 11 Oct 2026):
  - Cells change class "very frequently", and "forward and reverse transitions between states
    were equally probable". The usual route to scouting is swarm → lone cell → scout.
  - Scouts are "small groups of cells (1-20) isolated from the main colony".
  - Speeds, switching rates and path straightness appear only in figures (raw data on OSF), so
    there are no numbers to take.
  - Re-checked 12 Oct 2026: the text gives no share of scouts, loners or swarm cells in any
    condition, so B83's 10% at once is the user's choice.

**Berleman & Kirby 2009, *FEMS Microbiol. Rev.* 33:942 — Deciphering the hunting strategy of a bacterial wolfpack.**
[doi:10.1111/j.1574-6976.2009.00185.x](https://doi.org/10.1111/j.1574-6976.2009.00185.x) · checked from abstract
- Review of Myxo group hunting (the "wolf pack" idea). Supports sharing food from killed prey
  among nearby cells, not only the killer.

**Seef et al. 2021, *eLife* 10:e72409 — A Tad-like apparatus is required for contact-dependent prey killing.**
[doi:10.7554/eLife.72409](https://doi.org/10.7554/eLife.72409)
- Myxo kills *E. coli* on contact with a Tad-like machine, and A-motility is needed for
  invading prey colonies. This is our "kill on touch" rule. Same lab as the main paper; it is
  their ref. 41.
- Invasion (full text via Europe PMC, read 11 Oct 2026):
  - Single A-motile cells "penetrate the tightly-knitted E. coli colony", followed by larger
    groups, and kill prey on contact as they advance (Fig. 1a, 2a).
  - After each kill the cell "resumes movement" (Fig. 2b). Without A-motility cells "remain
    stuck at the border" (Fig. 1c).
  - This is the basis for B76: no bouncing back after contact, and Myxo crawling into colonies.
- Numbers, from the [full text on PMC (PMC8460266)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8460266/):
  - About 30% of contacts make the Myxo pause (Fig. 3c, n = 807), and more than 80% of
    pauses end in lysis (Fig. 4e, g), so about 26% of contacts kill.
  - Lysis comes within about 2 min of the killing machine assembling. Prey contents are lost
    at once, and empty "ghost" walls remain.
  - Myxo's generation time on prey is about 5.5 h (n = 16).

**Kearns & Shimkets 1998, *PNAS* — Chemotaxis in a gliding bacterium.**
[PMC21747](https://pmc.ncbi.nlm.nih.gov/articles/PMC21747) · PubMed 9751772 · checked from abstract
- Myxo moves up gradients of phosphatidylethanolamine (PE), a membrane lipid. It does this by
  reversing less often, needs FrzCD/FrzE, and adapts after about 1 hr.
- This is how our pull toward prey works (decision-log B32). E. coli membranes are rich in PE
  (textbook fact).
- The size of the reversal suppression isn't in the abstract, and the full text was blocked
  (11 Oct 2026), so `chemo_strength` stays tuned.
- **Kearns, Campbell & Shimkets 2000, *PNAS* ([PMC17230](https://pmc.ncbi.nlm.nih.gov/articles/PMC17230)),
  checked from a search summary:** fibrils (cell-surface appendages) are needed to respond to
  dilauroyl PE.
- **Sign conflict:** a later review ([PMC3194913](https://pmc.ncbi.nlm.nih.gov/articles/PMC3194913/))
  describes PE *increasing* reversals in starved cells, so the sign may depend on the PE species
  and on conditions.

**Kearns et al. 2001, *PNAS* 98:13990 — Identification of a developmental chemoattractant in *M. xanthus* through metabolic engineering.**
[PMC61154](https://pmc.ncbi.nlm.nih.gov/articles/PMC61154/) · doi:10.1073/pnas.251484598 · checked from the article page
- A specific PE (with the fatty acid 16:1ω5c) is the active attractant. It works at
  physiological amounts, and only under starvation: on nutrient-rich agar the response is
  blocked.
- So following the lipid smell is a starving-cell behaviour. It's the closest evidence for
  B72's stronger smell-following in hungry modes. No study singles out scouts.
- Used in B80: stringent cells follow the smell ×1.5 (the size is ours).

**Outer-membrane vesicles: Kulp & Kuehn 2010, *Annu. Rev. Microbiol.* 64:163 — Biological functions and biogenesis of secreted bacterial outer membrane vesicles.**
[doi:10.1146/annurev.micro.091208.073413](https://doi.org/10.1146/annurev.micro.091208.073413) ·
[biogenesis review (PMC7969528)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7969528/) · checked from abstract and a later review
- Gram-negative bacteria release outer-membrane vesicles. The review frames release partly as a
  stress response, so how much an undisturbed colony leaks is uncertain.
- Basis for the faint "colony smell" (decision-log B63).

**E. coli outer membrane is enriched in PE (1976 study of E. coli K-12 envelope lipids).**
[PMC217143](https://pmc.ncbi.nlm.nih.gov/articles/PMC217143) · checked from a search summary
- Compared with the inner membrane, the outer membrane is enriched in phosphatidylethanolamine
  and saturated fatty acids.
- Combined with Kearns & Shimkets 1998 (Myxo moves up PE gradients), this makes a PE-based pull
  toward living prey plausible (B63).

**Lloyd & Whitworth 2017, *Front. Microbiol.* 8:439 — *M. xanthus* can sense and respond to the quorum signals of potential prey.**
[PMC5348527](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5348527/) · checked from summary
- AHL quorum signals made by many prey bacteria boost Myxo motility and predation. E. coli
  doesn't make AHLs, so this isn't used for our prey.

**Thiery et al. 2022, *Cell Reports* 40:111340 — two secretion systems used in sequence to kill prey.**
[doi:10.1016/j.celrep.2022.111340](https://doi.org/10.1016/j.celrep.2022.111340) ·
[university record](https://hss-opus.ub.rub.de/opus4/frontdoor/index/index/year/2023/docId/10278) · checked from abstract and press release
- The Tad-like (Kil) system triggers prey death, then a needle-less type-3-like system
  (T3SS*) breaks the prey open. Both gather at the contact site, and both are needed to feed
  on live prey.
- Consistent with our single "pause → burst" step (B14). We don't model the two systems
  separately.

## Hunger and uptake

**Ferenci and colleagues: E. coli switches on high-affinity uptake when food is scarce ("hunger").**
[Death & Ferenci 1994, galactose-induced Mgl (PMC196350)](https://pmc.ncbi.nlm.nih.gov/articles/PMC196350) ·
[LamB in glucose-limited chemostats (PMC193235)](https://pmc.ncbi.nlm.nih.gov/articles/PMC193235) ·
[2022 review on hunger vs starvation](https://microbialcellfactories.biomedcentral.com/counter/pdf/10.1186/s12934-022-01909-y.pdf) · checked from summaries
- Under carbon limitation, E. coli raises scavenging systems (the LamB porin and the Mgl ABC
  transporter) that grab sugar at low concentrations.
- The 2022 review separates "hunger" (slower growth, scavenging switched on) from
  "starvation" (growth stops).
- **Caveat:** this is E. coli taking up sugar, while Myxo mainly takes up amino acids and
  peptides. B26 uses it as an analogy for "hungry cells absorb faster", not as a measured Myxo
  behaviour.

## The C-signal (why the paper doesn't use it)

**Boynton & Shimkets 2015, *Genes Dev.* 29:1903 — *Myxococcus* CsgA, *Drosophila* Sniffer and human HSD10 are cardiolipin phospholipases.**
[doi:10.1101/gad.268482.115](https://doi.org/10.1101/gad.268482.115) · checked from abstract
- CsgA, long thought to make the C-signal, is an enzyme that breaks down a membrane lipid
  (cardiolipin). That casts doubt on the C-signal as a contact signal, so our model, like the
  paper, has no C-signal.

## Starvation, growth and death

**Singer & Kaiser 1995, *Genes Dev.* 9:1633 — Ectopic production of (p)ppGpp initiates early development in *M. xanthus*.**
[doi:10.1101/gad.9.13.1633](https://doi.org/10.1101/gad.9.13.1633) · checked from abstract
- Amino-acid or carbon starvation raises (p)ppGpp, the stringent-response signal, and that
  switches Myxo from growth to development. This supports "no division while starving".

**Manoil & Kaiser 1980, *J. Bacteriol.*: two papers on (p)ppGpp in starving *M. xanthus*.**
[PMC293584](https://pmc.ncbi.nlm.nih.gov/articles/PMC293584) ·
[PMC293586](https://pmc.ncbi.nlm.nih.gov/articles/PMC293586) · checked from abstracts (via Europe PMC)
- Cultures starved for carbon and nitrogen "rapidly accumulated" the stringent-response
  signal. Limiting any of several classes of amino acids, or carbon-energy or phosphate,
  induced fruiting.
- No minutes are given. The trigger is food running out outside the cell, quickly; together
  with Harris 1998 this backs starting stringent mode from outside starvation.
- Applied in B83: starvation starts when prey food within reach runs out; stringent mode 30
  bio-min later (our number).

**Harris, Kaiser & Singer 1998, *Genes Dev.* 12:1022 — The guanosine nucleotide (p)ppGpp initiates development and A-factor production in *M. xanthus*.**
[doi:10.1101/gad.12.7.1022](https://doi.org/10.1101/gad.12.7.1022) · PMC316683 · checked from abstract (via Europe PMC)
- (p)ppGpp is made in response to amino-acid shortage (food running out outside the cell),
  via RelA. A mutant that can't make it stops in the first few hours of development, "the
  period of starvation recognition".
- So the real trigger of the stringent response is outside starvation, within hours, not an
  internal store running low. Relevant to when our stringent mode starts (B70–B72).

**Jelsbak & Søgaard-Andersen 2002, *PNAS* 99:2032 — Pattern formation by a cell surface-associated morphogen in *M. xanthus*.**
[PMC122314](https://pmc.ncbi.nlm.nih.gov/articles/PMC122314/) · checked from the article page
- Tracked single cells during starvation: mean gliding speed rose 1.5× between 0 and 15 h,
  from about 1.65 to 2.66 µm/min.
- Free-moving starving cells therefore get faster, not slower. This counts against B72's
  slower stringent cells.

**Sliusarenko, Zusman & Oster 2007, *J. Bacteriol.* 189:611 — Aggregation during fruiting body formation in *M. xanthus* is driven by reducing cell movement.**
[doi:10.1128/jb.01206-06](https://doi.org/10.1128/jb.01206-06) · PMC1797407 · checked from abstract (via Europe PMC)
- Cell velocities slow dramatically during aggregation, inside the aggregates, and that
  slowing (rather than reversal changes) gathers cells into fruiting bodies.
- Starving cells slow down only inside aggregates, which we don't model.

**Cell death during development: the numbers are disputed.**
[Wireman & Dworkin 1977, *J. Bacteriol.* (PMC235013)](https://pmc.ncbi.nlm.nih.gov/articles/PMC235013) ·
[PubMed 402359](https://pubmed.ncbi.nlm.nih.gov/402359)
- Older work reported that most cells (often quoted as 80–90%) lyse during fruiting body
  formation.
- O'Connor & Zusman (1988) argued the counting methods were flawed and found that at least 80%
  survive. Treat starvation death as uncertain; keep its rate an adjustable setting.
- **The usual picture of the fates**, from a review citing Nariya & Inouye 2008 and O'Connor &
  Zusman 1991:
  - about 60% (classic counts 60–80%) of starving cells lyse;
  - about 10% become spores in fruiting bodies;
  - the rest stay outside as peripheral rods.

  These are secondary figures, so check them before relying on them.
- Used in B80 (the famine exit): 70% lyse, 10% become spores, 20% stay as rods, a day into
  stringent mode. That split sits inside all three ranges.
- **Lee et al. 2012, *J. Bacteriol.* 194:3058
  ([PMC3370845](https://pmc.ncbi.nlm.nih.gov/articles/PMC3370845))**, checked from the abstract via
  Europe PMC:
  - cell lysis and aggregation both begin about 24 h after starvation starts development;
  - deleting *mazF* didn't reduce the lysis.

**O'Connor & Zusman 1991, *J. Bacteriol.* 173 (three papers) — peripheral rods.**
[PMC207943](https://pmc.ncbi.nlm.nih.gov/articles/PMC207943) ·
[PMC207944](https://pmc.ncbi.nlm.nih.gov/articles/PMC207944) ·
[PMC207945](https://pmc.ncbi.nlm.nih.gov/articles/PMC207945) · checked from abstracts (via a search summary)
- 10–20% of developing cells stay outside the fruiting bodies as "peripheral rods". These are
  a distinct, metabolically active, persister-like cell type that can regrow on low or
  passing nutrients without the cost of germinating a spore.

**Rajagopalan & Kroos 2014, *J. Bacteriol.* 196:2736 — Nutrient-regulated proteolysis of MrpC halts expression of genes important for commitment to sporulation during *M. xanthus* development.**
[doi:10.1128/jb.01692-14](https://doi.org/10.1128/jb.01692-14) · [PMC4135671](https://pmc.ncbi.nlm.nih.gov/articles/PMC4135671/) · checked from the abstract (via Europe PMC)
- Nutrients were added at set times after starvation. At about 24 h they partly broke up the
  fruiting bodies; by about 30 h compact fruiting bodies persisted and about tenfold more cells
  were committed to spores. The critical commitment period is about 24–30 h.
- Nutrients make the regulator MrpC break down fast, which halts sporulation genes: food that
  comes back early can reverse development.
- Fits our famine exit at 24 h (B80, from Lee 2012) as the point of no return.

**Hoang & Kroos 2018, *J. Bacteriol.* 200:e00456-18 — Ultrasensitive response of developing *M. xanthus* to the addition of nutrient medium correlates with the level of MrpC.**
[doi:10.1128/JB.00456-18](https://doi.org/10.1128/JB.00456-18) · [PMC6199472](https://pmc.ncbi.nlm.nih.gov/articles/PMC6199472/) · checked from the abstract (via Europe PMC)
- Two-fold dilutions of nutrient medium were added to starving cells before commitment. The
  response is switch-like: 12.5% medium let mounds re-form and spores rise steeply compared with
  25%. A small amount of food doesn't stop development; more than a threshold does.
- MrpC fell within 3 h of adding nutrients and recovered more after 12.5% than after 25%. The
  authors propose that a threshold MrpC level must be reached for development to go on.
- The basis for "a crumb shouldn't restart a cell's famine; only a real meal should" (B80 famine
  check). The papers measure nutrient medium, so the size of a "real meal" in our units is ours.
- Used in B81: stringent mode ends only once the store is back to 70 (the user's level).
- Since B83: starvation ends when prey food within reach is back above 3 units (the food
  around the cell, as the paper varied it); scraps from dead Myxo never end it.

**Himeoka, Gummesson, Sørensen, Svenningsen & Mitarai 2022, *mSphere* 7:e01006-21 — Distinct survival, growth lag, and rRNA degradation kinetics during long-term starvation for carbon or phosphate.**
[doi:10.1128/msphere.01006-21](https://doi.org/10.1128/msphere.01006-21) · [PMC9241543](https://pmc.ncbi.nlm.nih.gov/articles/PMC9241543/) · checked from the abstract (via Europe PMC)
- *E. coli* starved up to 28 days: the lag before regrowth got longer the longer cells had
  starved, even where rRNA per living cell stayed constant. Cells "remember" how long they
  starved.
- Loose backing for a recovery delay after a starved cell eats again. It's *E. coli*, and the
  abstract gives no lag values.

**Blackhart & Zusman 1985, *PNAS* 82:8767 — "Frizzy" genes of *M. xanthus* are involved in control of frequency of reversal of gliding motility.**
[doi:10.1073/pnas.82.24.8767](https://doi.org/10.1073/pnas.82.24.8767) · [PMC391518](https://pmc.ncbi.nlm.nih.gov/articles/PMC391518) · checked from the abstract (via Europe PMC)
- Mutants of the frz reversal system can't aggregate normally and make "frizzy" filaments
  instead of fruiting bodies (first described by Zusman 1982, *J. Bacteriol.* 150:1430).
- Most frz mutants reverse only about once every 2 h, frzD mutants about every 2.2 min; wild-type
  cells about every 6.8 min (close to Spormann & Kaiser 1999's ~6 min).
- So reversals matter for fruiting bodies too (B84 note for a later 3D project).

**E. coli starvation phases: Finkel 2006, *Nat. Rev. Microbiol.* — Long-term survival during stationary phase (GASP).**
[Review reproducing Finkel's phase figure (PMC8791185)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8791185) · checked from secondary sources
- Without food, cells go from stationary phase, to a death phase (90–99% die over days), to
  long-term stationary phase, where survivors persist for months, partly by feeding on dead
  cells. This is the basis for decision-log B34.

**GASP mutants: Zinser & Kolter 1999, *J. Bacteriol.* — Mutations enhancing amino acid catabolism confer a growth advantage in stationary phase.**
[PMC94102](https://pmc.ncbi.nlm.nih.gov/articles/PMC94102) · checked from the full text (via a summary), 16 Oct 2026
- In cultures starved for days to weeks (their examples: 10 days, about 2.5 weeks), mutants of
  increasing fitness take over in successive rounds. The first known one is an *rpoS* allele
  (rpoS819).
- The mutants grow faster on amino acids, which the authors propose lets them outcompete their
  parents on the amino acids released by dying cells (their model).
- So heritable survival arises during long starvation and works by growing on the dead, not by
  never dying. That's why B88 gives each cell its own persister chance instead of making whole
  lineages starvation-proof.

**How starving E. coli die: Schink et al. (Basan lab), single-cell time-lapse of carbon starvation.**
[PDF on the Basan lab site](https://basan.med.harvard.edu/resource/schinketal2021pdf) · checked from a search summary
- Within a few hours the cytoplasm contracts away from the wall (plasmolysis). Much later
  (about 26 h in their example) the membrane voltage collapses, and swelling and lysis follow
  soon after, because ion balance can't be kept without nutrients.
- This is the basis for decision-log B45 (dormant → death → short delay → burst).
- **Numbers** (from the 2021 preprint, doi:10.1101/2021.11.22.469587, via a search summary;
  the full texts were blocked on 11 Oct 2026):
  - lysis follows the voltage collapse after 2.0 ± 1.4 h;
  - viability falls exponentially to 0.1% within 10 days, a rate of about 0.69 per day
    (half-life about 1 day).
  - Both adopted in B80 (`starved_lysis_delay` 120 bio-min, `starvation_death_rate` 0.69 per
    bio-day).
  - The fall is exponential from early on, with no fixed lag before dying starts (same summary):
    adopted in B87 (`dormancy_before_death` 0). Single cells still die at different times (about
    26 h in their example), as a constant risk per hour gives.
  - The same risk for every cell means which cells survive is chance, not family: the basis for
    drawing each cell's persister flag at birth (B88).
- **Schink, Biselli, Ammar & Gerland 2019, *Cell Syst.* 9:64**
  ([doi:10.1016/j.cels.2019.06.003](https://doi.org/10.1016/j.cels.2019.06.003)), checked from the
  abstract via Europe PMC:
  - the death rate is set by the survivors' maintenance cost and by how much they recycle
    from dead cells' biomass;
  - so dead cells really do feed the living (B45).

**Nitta et al. 2000, *J. Bacteriol.* — Function of the σE regulon in dead-cell lysis in stationary-phase E. coli.**
[PubMed 10960110](https://pubmed.ncbi.nlm.nih.gov/10960110) · checked from a search summary
- Dead cells in stationary phase are lysed in a σE-dependent way, and released proteins
  build up in the medium. The authors propose this feeds the next generation.
- This supports "starved dead cells release food" (B34, B45).

**Bacterial growth efficiency: del Giorgio & Cole 1998, *Annu. Rev. Ecol. Syst.* 29:503.**
[doi:10.1146/annurev.ecolsys.29.1.503](https://doi.org/10.1146/annurev.ecolsys.29.1.503) · checked from abstract
- The fraction of eaten carbon that becomes new bacterial biomass ranges from under 5% to
  about 60%, and is near 50% where food is rich. We used 30% (B21), then 50% (B75: prey
  contents are rich food), and 30% again since B85 so that each prey feeds fewer hunters; both are
  inside the measured range.

**Rosenzweig & MacArthur 1963, *Am. Nat.* 97:209 — Graphical representation and stability conditions of predator–prey interactions.**
[doi:10.1086/282272](https://doi.org/10.1086/282272) · reference checked on Crossref (15 Oct 2026); the result
below is the standard textbook account, not re-read
- Prey grow toward a ceiling, and predators eat more as prey get commoner, up to a limit. Plotted
  as two curves, the balance point is steady when the predators need many prey to hold their
  numbers, and the populations cycle when they need few.
- So predators that convert food less well or die faster (B85) push toward a steadier balance,
  with smaller swings.

**Rosenzweig 1971, *Science* 171:385 — Paradox of enrichment: destabilization of exploitation ecosystems in ecological time.**
[doi:10.1126/science.171.3969.385](https://doi.org/10.1126/science.171.3969.385) ·
[PubMed 5538935](https://pubmed.ncbi.nlm.nih.gov/5538935) · checked from abstract (Europe PMC, 15 Oct 2026)
- In six models of a predator and its prey, more food for the prey tends to destroy the steady
  state: the swings grow. The reverse is why a poorer ground (B85) should damp our cycles.

**The 10% rule: Lindeman 1942, *Ecology* 23:399.**
[JSTOR, doi:10.2307/1930126](https://doi.org/10.2307/1930126) (DOI from memory, not confirmed)
- About 10% of energy passes between whole trophic levels of an ecosystem. It's an ecosystem
  average, so we don't use it for one bacterium eating another.

## Sizes and rates

***E. coli* size and doubling time (BioNumbers).**
[Dimensions of *E. coli* K-12](https://bionumbers.hms.harvard.edu/bionumber.aspx?id=104113) ·
[Length and radius vs doubling time](https://bionumbers.hms.harvard.edu/bionumber.aspx?id=106305)
- Typical cell: about 2 µm long, about 0.8–1 µm wide, about 1 µm³. Length runs 2–4 µm and
  depends on growth rate, which fits "born at about 2 µm, divides at about 4 µm".
- The shortest doubling time is about 20 min in rich medium at 37 °C. On agar at room
  temperature it is slower.

***M. xanthus* size.**
[Frontiers in Microbiology 2013 (doi:10.3389/fmicb.2013.00335)](https://doi.org/10.3389/fmicb.2013.00335) ·
[Wikipedia](https://en.wikipedia.org/wiki/Myxococcus_xanthus)
- Growing cells are 5–7 µm long and about 0.5 µm wide. The main paper uses 5 µm, and measured
  0.7 µm width.
- Older notes also cite Shi & Zusman 1993 and Kaiser, Robinson & Kroos 2010; I could not
  re-check those online.

**Spormann & Kaiser 1999, *J. Bacteriol.* — Gliding mutants of *M. xanthus* with high reversal frequencies and small displacements.**
[PMC93688](https://pmc.ncbi.nlm.nih.gov/articles/PMC93688) · checked from the abstract (via Europe PMC)
- Wild-type cells glide at 4.4 µm/min and reverse 0.17 times per minute (about every 6 min).
- Our model uses the paper's 4 µm/min. 4.4 µm/min is the measured basis for a lone scout's
  speed (about 1.1×, not 1.2×); adopted in B80.
- Checked against our model (11 Oct 2026): 60 single cells in the empty live world reverse about
  every 12 min (0.084 per min), about half the measured rate. A calm cell's reversal rate in the
  paper's rule is very low (0.007 per min); most of these reversals come from brief frustration
  when cells meet or turn onto trails.

***M. xanthus* doubling time.**
[JoVE protocol (doi:10.3791/57860)](https://www.jove.com/t/57860)
- About 4–6 h in standard rich medium. Zusman & Rosenberg 1971 measured about 6.5 h (390 min)
  at 30 °C.
- Seef et al. 2021 measured about 5.5 h for Myxo feeding on prey (see above).
- So Myxo divides roughly 12–18× more slowly than *E. coli*.

## Cell-to-cell variation in E. coli growth

**Spread of division length (BioNumbers 110034).**
[BioNumbers 110034](https://bionumbers.hms.harvard.edu/bionumber.aspx?id=110034) ·
[an older multi-strain study (PMC221788)](https://pmc.ncbi.nlm.nih.gov/articles/PMC221788) · checked from a search summary
- The coefficient of variation of length at division is about 0.10 for *E. coli* B/r and
  *Salmonella*. The older study averaged 13.5% across strains and growth rates.
- This backs `ecoli_divide_noise` (±10%, B53) as measured.

**Wang et al. 2010, *Curr. Biol.* — Robust growth of *Escherichia coli* (the "mother machine").**
[PMC2902570](https://pmc.ncbi.nlm.nih.gov/articles/PMC2902570) · checked from a search summary
- Single cells were tracked for hundreds of generations in a microfluidic device. Growth speed
  fluctuates from one cycle to the next and isn't carried over: a cell "forgets" its previous
  speed at division, and daughters match mothers statistically.
- This is the basis for redrawing each newborn's growth speed (decision-log B55).

**Wallden et al. 2016, *Cell* and Grilli et al. 2018, *Front. Microbiol.* — growth-rate variability and size control.**
[Wallden 2016 (PDF)](https://elflab.icm.uu.se/lore/ref/Cell-2016-Wallden.pdf) ·
[Grilli 2018](https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2018.01541/full) · checked from search summaries
- Differences in growth speed drive much of the variation in generation time and division
  size. Grilli's reanalysis notes that earlier work often neglected this.
- A review quotes a generation-time CV of about 0.29; its original source isn't traced.
- This supports raising speed variation to ±20% (B55).

## Division, storage and sharing (energy rules)

**Taheri-Araghi et al. 2015, *Curr. Biol.* 25:385 — Cell-size control and homeostasis in bacteria.**
[doi:10.1016/j.cub.2014.12.009](https://doi.org/10.1016/j.cub.2014.12.009) ·
[PMC4323405](https://pmc.ncbi.nlm.nih.gov/articles/PMC4323405) · checked from abstract
- Tracked hundreds of thousands of single *E. coli* and *B. subtilis* cells. Each adds a
  roughly constant amount between birth and division, whatever its birth size (the "adder").
- This is the basis for our fixed division cost of 50. Caveat: not measured in Myxo.

**Schumacher et al. 2017, *Dev. Cell* 41:299 — The PomXYZ proteins self-organize on the bacterial nucleoid to stimulate cell division.**
[doi:10.1016/j.devcel.2017.04.011](https://doi.org/10.1016/j.devcel.2017.04.011) ·
[arXiv preprint](https://arxiv.org/abs/1801.09549) · checked from preprint and summaries
- *M. xanthus* divides at mid-cell, guided by the PomX, PomY and PomZ proteins. This is the
  basis for splitting the leftover food equally between daughters.

**Hoiczyk et al. 2009, *Mol. Microbiol.* 74:497 — Lipid body formation plays a central role in cell fate determination during development of *M. xanthus*.**
[doi:10.1111/j.1365-2958.2009.06879.x](https://doi.org/10.1111/j.1365-2958.2009.06879.x) ·
[PMC2877170](https://pmc.ncbi.nlm.nih.gov/articles/PMC2877170) · checked from abstract
- Myxo stores fuel as lipid bodies. In starving cells, those that form lipid bodies become
  spores and burn them as fuel during development.
- This is the basis for our reserve zone (100–110). The 110 cap itself is our assumption.

**Bacterial storage polymers (glycogen, PHB): general background.**
[Frontiers in Microbiology 2016 (PDF)](https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2016.00966/pdf) · checked from summary
- Bacteria turn surplus carbon into storage polymers and use them when food runs out. Stores
  can reach 70% of dry weight in some species, but no general fixed maximum exists.

**Outer membrane exchange (OME): Ducret et al. 2013, *eLife* 2:e00868; Wall lab reviews.**
[Ducret 2013 (doi:10.7554/eLife.00868)](https://doi.org/10.7554/eLife.00868) ·
[Wall lab review (PMC7744404)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7744404/) · checked from summaries
- Touching, aligned Myxo cells with matching TraA proteins swap outer-membrane proteins and
  lipids. Ducret 2013 is the main paper's ref. 5.
- We decided not to use this for food sharing (decision-log B28), since what moves is
  membrane, not food.

***M. xanthus* genome (strain DK1622): Goldman et al. 2006, *PNAS* 103:15200.**
[PubMed 17015832](https://pubmed.ncbi.nlm.nih.gov/17015832) · [NCBI NC_008095](https://www.ncbi.nlm.nih.gov/nuccore/NC_008095)
- One circular chromosome of 9,139,763 bp. Gene duplication expanded signalling and sensing
  genes. Background only; not used in the model.
