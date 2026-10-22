# When satellite datasets disagree: a methodological note for EUDR screening

Product 4 of the EUDR portfolio. Regulation (EU) 2023/1115, cutoff date 31 December 2020.

**Status of the numbers:** results from one run on six synthetic test boxes, on 22 October 2026. The boxes are not real suppliers, what is grown inside each one is not verified, and nothing in this note is a compliance verdict.

## 1. The question

A screening tool flags a supplier. The supplier says the flag is wrong. What does a compliance team do?

The answer depends on a fact that vendor demos rarely show: the public datasets used for EUDR screening often do not agree with each other about the same piece of land. This note measures how much they disagree, shows where and why, and proposes a decision protocol for when they do.

The stakes are asymmetric. A false positive can cost a commercial relationship. A false negative can cost fines of at least 4% of EU turnover (Art. 25) and, under the zero-tolerance logic of Art. 9, any deforestation or forest degradation on a plot disqualifies the products from it.

## 2. What was measured

Six boxes of about 0.2 by 0.2 degrees (roughly 44,000 to 49,000 ha each), one per regional commodity context:

| Box | Commodity context | Country | Centre (lon, lat) |
|---|---|---|---|
| WOOD-MISIONES | wood (pine plantations) | AR | -54.60, -26.40 |
| SOY-PARA | soy | BR | -54.75, -2.75 |
| CATTLE-PARA | cattle | BR | -52.00, -6.65 |
| COFFEE-PERU | coffee | PE | -77.00, -6.00 |
| COCOA-CIV | cocoa | CI | -6.60, 5.78 |
| PALM-KALIMANTAN | oil palm | ID | 111.62, -2.68 |

The commodity labels come from regional knowledge, not from verification. They describe the dominant context of the area, not what is grown in every pixel.

Datasets, all read in Google Earth Engine:

| Dataset | What it says | Resolution | Used for |
|---|---|---|---|
| JRC Global Forest Cover 2020 V3 (`JRC/GFC2020/V3`) | Forest or not at 31/12/2020 | 10 m | Baseline: was it forest at the cutoff |
| Hansen Global Forest Change v1.13 (`UMD/hansen/global_forest_change_2025_v1_13`) | Tree cover loss, year by year | 30 m | Loss after 2020, tree cover of 10% and 30% thresholds |
| JRC Tropical Moist Forests v1_2025 | Deforestation year and degradation year | 30 m | Deforestation or degradation after 2020 |
| RADD alerts (`projects/radar-wur/raddalert/v1`) | Sentinel-1 radar alerts | 10 m | Alerts after 2020, primary humid tropical forest only |
| Forest Data Partnership models (`model_2026a`) | Probability of cocoa, coffee, oil palm | 10 m | Context: does the land look like the commodity |

For each box the script measures hectares flagged after 31/12/2020 by each dataset, and how many hectares are flagged by one, two or three of Hansen (30% tree cover), TMF and RADD on a common 30 m grid.

## 3. What the numbers show

Hectares flagged after 31/12/2020 (Hansen at 30% tree cover; TMF is deforestation plus degradation; RADD is alerts of any confidence):

| Box | Box ha | Forest at 2020 (JRC) | Hansen loss | TMF defor. | TMF degrad. | RADD alerts |
|---|---|---|---|---|---|---|
| WOOD-MISIONES | 44,300 | 32,974 | 2,202 | 14 | 17 | not monitored |
| SOY-PARA | 49,400 | 15,742 | 4,104 | 1,812 | 1,418 | 886 |
| CATTLE-PARA | 49,125 | 11,713 | 2,177 | 594 | 1,271 | 755 |
| COFFEE-PERU | 49,186 | 14,692 | 3,308 | 666 | 394 | 873 |
| COCOA-CIV | 49,206 | 854 | 1,078 | 166 | 67 | not monitored |
| PALM-KALIMANTAN | 49,403 | 14,510 | 1,970 | 1,243 | 601 | 126 |

Agreement among Hansen, TMF and RADD, in hectares:

| Box | Flagged by 1 dataset | By 2 | By all 3 | Share of flagged area that 2 or more datasets agree on |
|---|---|---|---|---|
| WOOD-MISIONES | 2,201 | 16 | 0 (RADD absent) | 1% |
| SOY-PARA | 3,685 | 1,427 | 617 | 36% |
| CATTLE-PARA | 3,234 | 688 | 145 | 20% |
| COFFEE-PERU | 3,563 | 658 | 227 | 20% |
| COCOA-CIV | 1,227 | 42 | 0 (RADD absent) | 3% |
| PALM-KALIMANTAN | 1,719 | 914 | 135 | 38% |

Three readings follow.

**Most flagged area is flagged by one dataset only.** In the four boxes where all three datasets operate, only 20% to 38% of the flagged area is flagged by two or more, and 4% to 11% by all three. Which dataset a tool relies on largely decides the answer.

**The datasets disagree about what counts as forest.** The share of Hansen loss that falls on land JRC classes as forest at 2020 is 96% in Misiones, 56% to 60% in the Pará and Kalimantan boxes, 30% in the Peru coffee box and only 3% in the Côte d'Ivoire cocoa box. The JRC map sees 854 ha of forest in a 49,206 ha cocoa box, while Hansen sees 1,078 ha of loss and the cocoa model gives a probability above 0.5 on about 26,300 ha. Tree cover is changing there, but most of it is not "forest" in the sense the baseline map uses. Changing Hansen's tree cover threshold from 30% to 10% adds 49% more flagged area in this box, against 1% to 6% in the others.

**Coverage gaps change what "no alert" means.** RADD monitors primary humid tropical forest only. In Misiones and Côte d'Ivoire it monitors 0 ha, so "no RADD alerts" there means "not monitored", not "no change". In the other boxes RADD monitors between 12% and 19% of the box. The Forest Data Partnership models only apply between 24 degrees north and south, so they do not apply in Misiones (latitude -26.4).

### The Misiones case

In Misiones, Hansen flags about 2,200 ha of tree cover loss after 2020, 96% of it on land JRC classes as forest at 2020. TMF flags 14 ha of deforestation and 17 ha of degradation, all in the north west corner of the box. RADD does not monitor the area.

One reading, which is a hypothesis and not a finding: much of the Hansen loss is harvesting of planted pine, which Hansen records as tree cover loss. Under Art. 2, deforestation is the conversion of forest to agricultural use, and forest degradation is the conversion of primary or naturally regenerating forest into plantation forests or other wooded land. The harvest of a plantation forest that is replanted is neither. But the datasets used here cannot distinguish harvest from conversion, and the test cannot rule out that some of the 2,200 ha is real conversion.

This also puts Product 2 in context. Product 2 returned NOT_COMPLIANT for a Misiones box because the Art. 9 zero-tolerance rule means a few hectares of TMF deforestation or degradation are enough. This product shows that Hansen sees about 70 times more area (2,202 ha against TMF's 31 ha) in a larger box around the same area, and that the two do not explain each other. Neither result is a determination on its own.

## 4. Why the datasets disagree

**Definitions.** Art. 2 defines "forest" as land spanning more than 0.5 hectares with trees higher than 5 metres and a canopy cover of more than 10%, or trees able to reach those thresholds in situ, excluding land that is predominantly under agricultural or urban land use. An "agricultural plantation" is land with tree stands in agricultural production systems, including fruit tree plantations, oil palm plantations and agroforestry systems where crops are grown under tree cover, and it is excluded from the definition of forest. Deforestation is the conversion of forest to agricultural use. Forest degradation is the conversion of primary or naturally regenerating forest into plantation forests or other wooded land, or of primary forest into planted forests.

Hansen measures tree cover loss, which fires on plantation harvest, agroforestry renewal, fire and natural disturbance as well as on deforestation. JRC GFC2020 produces a forest map at the cutoff. TMF works with tropical moist forest only and tracks disturbance events. RADD detects disturbance in primary humid tropical forest. Each answers a different question, and none of them answers the legal one (was this forest, as defined in Art. 2, converted to agricultural use after 31/12/2020?) directly.

The wording of Art. 2 above was read from a secondary copy of the consolidated text and should be checked against EUR-Lex before this note is cited.

**Resolution.** Areas here are computed at each dataset's own resolution (10 m or 30 m) and agreement on a common 30 m grid. Small clearings can be seen by a 10 m dataset and missed by a 30 m one.

**Dates.** The cutoff is a date, not a year. Hansen and TMF report year of loss. A year-level flag for 2020 cannot say whether a clearing happened before or after 31 December. This note uses years greater than 2020 for the annual datasets, which means an event late in 2020 is treated as before the cutoff, and RADD dates greater than 21000, assuming the date band is encoded as year and day of year.

**Coverage.** Section 3 above. A dataset that does not cover the plot is silent, not clean.

## 5. A decision protocol for when datasets disagree

This is a methodological proposal, not legal advice and not an official procedure. Its goal is that two people looking at the same flag reach the same next step, and that the reasoning is written down.

Record first, for every plot: the datasets and versions used, the date of the run, the thresholds, and which datasets cover the plot.

| Situation | What it means | Proposed next step |
|---|---|---|
| No dataset flags change, and all cover the plot | No change detected by these sources. Not a guarantee for the whole plot or for what the sources cannot see | Document the sources and the date. Keep the evidence for five years (Art. 4) |
| Exactly one dataset flags | Weakest evidence. May be a definition difference, not deforestation | Do not conclude either way. Check what that dataset measures. Look at high resolution imagery from before and after the cutoff. Ask the supplier for dated evidence (planting, harvest, replanting records) |
| Two or more datasets flag the same area | Stronger evidence, especially when they use different sensors | Treat as high risk and escalate. Under Art. 9 any deforestation or degradation on the plot disqualifies its products, so the burden moves to proving the area was not forest at the cutoff or was not converted |
| A dataset does not cover the plot | Silence, not a clean result | Record the gap. Rely on the datasets that do cover it and on imagery. Do not count a missing alert as a negative |
| Land is tree crop or agroforestry (cocoa, coffee, oil palm, rubber) | Tree cover loss may be renewal of an agricultural plantation, which Art. 2 excludes from forest | Establish what the land was at 31/12/2020. If it was already an agricultural plantation, the loss is not deforestation. If it was forest, it is |
| Supplier disputes a flag | Both sides may be right about different things | Ask for plot-level geometry and dated evidence. Re-run the same datasets on the corrected geometry. Keep both versions and the decision |

## 6. Limits

- Six synthetic boxes, one run. This is not a statistical study of dataset accuracy.
- The commodity inside each box is not verified.
- No ground truth. Disagreement does not show which dataset is right.
- Hansen is tree cover loss, not deforestation. TMF covers tropical moist forest only. RADD covers primary humid tropical forest only.
- RADD date encoding is assumed to be year and day of year. The raw date ranges in the output are consistent with this (for example 26285 for day 285 of 2026), but this was checked by plausibility, not documentation.
- The Forest Data Partnership model outputs are probabilities, not observations, and there is no soy or wood model.
- JRC also publishes a GFC2020 subtype layer that separates primary, naturally regenerating and planted forest. It was not used here and would be the logical next check for Misiones.

## 7. Reproduce

`scripts/product4_comparison.js` runs in the Earth Engine Code Editor and exports `data/EUDR_product4_dataset_comparison.csv`. `scripts/product4_thumbnails.js` generates the image panels in `images/`. Image panels are shown for two boxes only: Misiones and Pará (soy).
