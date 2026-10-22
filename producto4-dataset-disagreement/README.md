# Product 4: When satellite datasets disagree

Part of the EUDR portfolio (Regulation (EU) 2023/1115, cutoff 31 December 2020).

**View the results:** https://leonardoscarpa.github.io/validador-geometrias-eudr/product4_dataset_disagreement_en.html

**Read the note:** [METHODOLOGICAL_NOTE.md](METHODOLOGICAL_NOTE.md)

## What it is

EUDR screening relies on public satellite datasets. This product measures how much four of them disagree about the same land, explains why, and proposes a decision protocol for a compliance team when a flag is disputed.

It runs Hansen Global Forest Change, JRC Tropical Moist Forests, RADD radar alerts and the JRC 2020 forest map over six synthetic test boxes of about 48,000 ha, one per commodity context (wood, soy, cattle, coffee, cocoa, oil palm). The Forest Data Partnership commodity models are used as context where they apply.

## Main findings

- In the four boxes where Hansen, TMF and RADD all operate, only 20% to 38% of the flagged area is flagged by two or more datasets, and 4% to 11% by all three.
- In Misiones (Argentina), Hansen flags about 2,200 ha of tree cover loss after 2020 and TMF flags 31 ha. RADD does not monitor the area.
- In the Côte d'Ivoire cocoa box, 3% of Hansen loss falls on land the JRC map calls forest at 2020, so the datasets disagree mostly about what counts as forest.
- "No RADD alert" means "not monitored" wherever RADD has no coverage (0 ha in Misiones and Côte d'Ivoire).

## Contents

```
producto4-dataset-disagreement/
├── METHODOLOGICAL_NOTE.md          # the full note and decision protocol
├── scripts/
│   ├── product4_comparison.js      # Earth Engine script, exports the CSV
│   └── product4_thumbnails.js      # Earth Engine script, generates the image panels
├── data/
│   └── EUDR_product4_dataset_comparison.csv
└── images/                         # panels for Misiones and Pará (Hansen, TMF, RADD, agreement)
```

The viewer page is `product4_dataset_disagreement_en.html` in the repository root.

## Reproduce

Paste `scripts/product4_comparison.js` into the Earth Engine Code Editor, run it, and start the export task in the Tasks tab. It prints the results and exports the CSV. `scripts/product4_thumbnails.js` prints links to the image panels; save each PNG with the name shown.

## Limits

- Six synthetic boxes and one run, on 22 October 2026. Not a statistical study of dataset accuracy.
- The commodity inside each box is a regional label and was not verified.
- There is no ground truth, so disagreement does not show which dataset is right.
- Hansen measures tree cover loss, not deforestation. TMF covers tropical moist forest only. RADD covers primary humid tropical forest only.
- RADD dates are assumed to be year and day of year. The raw output is consistent with that, but it was checked by plausibility, not documentation.
- The Article 2 wording used in the note was read from a secondary copy of the consolidated text. Check it against EUR-Lex before citing.
- The decision protocol is a methodological proposal, not legal advice and not an official procedure.
- Nothing here is a compliance verdict.
