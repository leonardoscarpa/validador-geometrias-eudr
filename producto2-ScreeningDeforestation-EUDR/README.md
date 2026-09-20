# EUDR Deforestation Screening

Product 2 of the EUDR compliance portfolio. Checks supplier plots against the
EUDR's 31 December 2020 cutoff date using real Google Earth Engine satellite
data — not a single fixed snapshot.

**Live results viewer**: [producto2_resultados_en.html](../producto2_resultados_en.html)

## Why this isn't just "load GFC2020 and check a pixel"

`JRC/GFC2020/V3` — the dataset most portfolio demos reach for — is a single
fixed snapshot at 31/12/2020. It confirms forest was present that day, but it
cannot say whether that forest was cleared afterward. On its own, it cannot
answer the only question the EUDR actually asks: *was this parcel deforested
or degraded after the cutoff?*

This script uses **JRC Tropical Moist Forest (TMF) v1_2025** instead, which
tracks two independent change layers pixel by pixel since 1990:

- `DeforestationYear` — the calendar year forest was first cleared
- `DegradationYear` — the calendar year forest was first structurally degraded

## Why degradation is checked, not just deforestation

Article 2 defines "deforestation-free" for wood specifically as land with no
deforestation after the cutoff **and** wood "harvested without inducing
forest degradation" after that date. Standing forest isn't enough on its own
for the focus commodity of this portfolio. Most public demos only check
deforestation — this one checks both TMF layers.

## No tolerance threshold

Article 9 disqualifies a parcel automatically at any trace of deforestation
or degradation post-cutoff — there is no tolerated percentage of affected
area. The script mirrors that exactly: a single flagged pixel anywhere in
the geometry is enough to return `NOT_COMPLIANT`.

## The third state: `NEEDS_REVIEW_NO_TMF_COVERAGE`

TMF covers the tropical moist forest domain. Where it has no classification
at all for a given area, the script does not default to "compliant" in
silence — it returns an explicit third verdict, distinct from both
`COMPLIANT` and `NOT_COMPLIANT`, so a gap in the data source is never
mistaken for a clean result.

## How to run it

1. Open [code.earthengine.google.com](https://code.earthengine.google.com)
   with a Google Earth Engine account.
2. Paste the contents of `producto2_screening.js` into the Code Editor.
3. Click **Run**.
4. Results print to the Console and render on the map. To export the full
   GeoJSON, run the `Export.table.toDrive` task from the **Tasks** tab.

To use your own parcels instead of the built-in test set: upload a GeoJSON
as an Earth Engine asset (Assets tab → New → Table upload), then replace the
`parcels` FeatureCollection at the top of the script with
`ee.FeatureCollection('users/YOUR_USERNAME/YOUR_ASSET')`. No other part of
the script needs to change, as long as your properties use the same field
names as Product 1's output (`ParcelID`, `ProducerCountry`, etc.).

## Real test results

Three test plots, real Earth Engine output, not invented figures:

| Plot | Location | Area | Deforestation post-2020 | Degradation post-2020 | Verdict |
|---|---|---|---|---|---|
| `MSNS-TEST-1` | Misiones, near Iguazú | 24,880 ha | Yes | Yes | **NOT_COMPLIANT** |
| `CTES-TEST-1` | Corrientes | 24,512 ha | No | No | COMPLIANT |
| `SDE-COPO-TEST-1` | Santiago del Estero, Copo dept. | 100,033 ha | No | No | COMPLIANT |

The interesting result isn't the one that looks obvious. Misiones is
generally associated with well-preserved forest near Iguazú, yet a 24,880 ha
test box there returned `NOT_COMPLIANT` on both layers. Santiago del Estero,
Argentina's most-deforested province in every annual Greenpeace report from
2021 to 2025, returned clean on a box four times larger. A first Salta test
(department Anta, also a known deforestation hotspot) likewise came back
compliant before this Santiago del Estero test was added — see commit
history for that earlier attempt.

This does not prove Santiago del Estero is deforestation-free — a 100,000 ha
box, however large, can still miss the exact site of a real clearing event.
It demonstrates the actual point of the product: regional reputation is not
a substitute for parcel-level verification, and the two can disagree.

## Known limitations (documented on purpose)

- **Box size vs. precision.** These are synthetic test boxes, not real
  supplier parcels with known coordinates. A "compliant" result reflects "no
  change detected within this specific box," not a guarantee for the wider
  region. Product 1 in this portfolio is what validates real parcel geometry
  submitted by an actual supplier.
- **TMF's domain.** TMF is built for tropical moist forest. All three test
  boxes returned `tmf_has_coverage: true`, including the drier Chaco-margin
  areas — coverage turned out broader than expected going in. This is worth
  re-testing before treating it as a general rule for any specific real
  sourcing region.
- **Scale.** Zonal statistics run at TMF's native 30 m resolution
  (`reduceRegion`, `scale: 30`). This is adequate for a portfolio-scale
  screening tool, not a substitute for a full audit-grade pixel export.

## Files in this folder

- `producto2_screening.js` — the Earth Engine Code Editor script
- `README.md` — this file

The results viewer (`producto2_resultados_en.html`) lives loose in the repo
root, not in this folder, so GitHub Pages serves it at a clean URL — same
convention as Products 1 and 3.
