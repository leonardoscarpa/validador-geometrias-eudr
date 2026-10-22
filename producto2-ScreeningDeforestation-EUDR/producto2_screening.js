// ============================================================================
// PRODUCT 2: EUDR Deforestation Screening
// Checks each parcel against the 31/12/2020 cutoff date.
//
// KEY DESIGN DECISION: JRC/GFC2020/V3 is a SNAPSHOT at 31/12/2020
// (a single instant, band "Map" = 1 if there was forest). On its own it
// CANNOT tell us whether that forest was cleared AFTER that date. For that
// we use JRC Tropical Moist Forest (TMF) v1_2025, which does have
// "deforestation year" and "degradation year" layers pixel by pixel.
//
// FOR WOOD (the focus commodity of this portfolio), Art. 2 of the
// Regulation requires that the wood "has been harvested without inducing
// forest degradation" after the cutoff. Not having deforested is not enough.
// That is why this script checks DEFORESTATION *and* DEGRADATION, not just
// one of the two. Most demos you will see out there only check deforestation.
//
// ZERO-THRESHOLD DISQUALIFICATION (Art. 9): a single pixel of post-2020
// deforestation or degradation inside the polygon disqualifies the WHOLE
// parcel. There is no tolerance percentage.
//
// KNOWN LIMITATION (documented on purpose, not a hidden bug): TMF covers the
// "tropical moist forest" domain. Misiones (Paranaense rainforest) likely
// falls inside; parts of Corrientes, drier and further south, may fall
// OUTSIDE the area mapped by TMF. When that happens the script does NOT
// silently assume "compliant". It returns "NEEDS_REVIEW_NO_TMF_COVERAGE" so
// it is clear that another data source is needed there.
// ============================================================================


// ---------------------------------------------------------------------------
// 1) TEST PARCELS
// ---------------------------------------------------------------------------
// Three synthetic parcels to test the script: one in Misiones (rainforest,
// most likely covered by TMF), one in Corrientes (further south, may fall
// outside the TMF domain), and one in Santiago del Estero (a well-documented
// active clearing zone, to confirm the script DOES detect a real case).
// Enlarged boxes (~16x16 km and ~33x33 km) so the result is easier to see on
// the map and to increase the chance of capturing actually cleared area.

var parcels = ee.FeatureCollection([
  ee.Feature(
    ee.Geometry.Polygon([[
      [-54.675, -26.325], [-54.525, -26.325],
      [-54.525, -26.475], [-54.675, -26.475], [-54.675, -26.325]
    ]]),
    {ParcelID: 'MSNS-TEST-1', ProducerCountry: 'AR',
     CommonName: 'Pine', ScientificName: 'Pinus taeda'}
  ),
  ee.Feature(
    ee.Geometry.Polygon([[
      [-56.075, -27.985], [-55.925, -27.985],
      [-55.925, -28.135], [-56.075, -28.135], [-56.075, -27.985]
    ]]),
    {ParcelID: 'CTES-TEST-1', ProducerCountry: 'AR',
     CommonName: 'Eucalyptus', ScientificName: 'Eucalyptus grandis'}
  ),
  // Box in the Copo department, Santiago del Estero. Unlike Anta (Salta),
  // tested earlier and returned COMPLIANT, Copo is explicitly cited as one of
  // the areas "most affected" by recent clearing (together with Alberdi,
  // Pellegrini and Moreno), and Santiago del Estero is, in EVERY annual
  // 2021-2025 report I found, the province with the most hectares cleared in
  // the country, more than Salta in recent years, even though Salta has a
  // larger historical total. ~33x33 km box centered on the department to
  // maximize the chance of capturing genuinely cleared area after 2020.
  ee.Feature(
    ee.Geometry.Polygon([[
      [-62.981, -25.656], [-62.681, -25.656],
      [-62.681, -25.956], [-62.981, -25.956], [-62.981, -25.656]
    ]]),
    {ParcelID: 'SDE-COPO-TEST-1', ProducerCountry: 'AR',
     CommonName: 'N/A (negative control)', ScientificName: 'N/A'}
  )
]);

// --- TO USE YOUR OWN PARCELS (the output.geojson from Product 1) ---
// 1. Left panel > "Assets" tab > "NEW" > "Table upload" > upload the
//    .geojson. It takes a couple of minutes to process.
// 2. Replace the block above with:
//      var parcels = ee.FeatureCollection('users/YOUR_USER/YOUR_ASSET');
// 3. The rest of the script needs no other change, as long as your
//    properties use the same names (ParcelID, ProducerCountry, etc.)
//    that already come from Product 1.


// ---------------------------------------------------------------------------
// 2) DATASETS
// ---------------------------------------------------------------------------

var CUTOFF_YEAR = 2020;

// Forest snapshot at 31/12/2020. Used only as visual CONTEXT, not for the
// compliant / not compliant decision (TMF does that, below).
var gfc2020 = ee.Image('JRC/GFC2020/V3').select('Map');

// TMF: deforestation year and degradation year, pixel by pixel.
// mosaic() joins the continental tiles into one continuous image.
var tmfDeforYear = ee.ImageCollection('projects/JRC/TMF/v1_2025/DeforestationYear').mosaic();
var tmfDegradYear = ee.ImageCollection('projects/JRC/TMF/v1_2025/DegradationYear').mosaic();

// Transition Map: used ONLY to know whether TMF has coverage here
// (any category counts as "coverage", even "not forest").
// Unlike DeforestationYear, which only has data where deforestation DID
// happen, the Transition Map classifies everything inside the TMF domain,
// which is why it is the one that works for detecting "no data".
var tmfTransition = ee.ImageCollection('projects/JRC/TMF/v1_2025/TransitionMap_Subtypes').mosaic();


// ---------------------------------------------------------------------------
// 3) PER-PARCEL EVALUATION
// ---------------------------------------------------------------------------

function evaluateParcel(feature) {
  var geom = feature.geometry();

  // .unmask(0): pixels never deforested/degraded come back "empty" (no data)
  // in TMF, not 0. We make them an explicit 0 BEFORE comparing, so
  // reduceRegion does not confuse "it never happened" with "there is no data".
  var deforAfterCutoff = tmfDeforYear.unmask(0).gt(CUTOFF_YEAR);
  var degradAfterCutoff = tmfDegradYear.unmask(0).gt(CUTOFF_YEAR);

  // .mask() of the Transition Map: 1 where TMF has any classification,
  // 0 where the pixel is outside its domain (tropical moist forest).
  var hasCoverageImg = tmfTransition.mask();

  var combined = ee.Image.cat([
    deforAfterCutoff.rename('defor_flag'),
    degradAfterCutoff.rename('degrad_flag'),
    hasCoverageImg.rename('has_coverage')
  ]);

  var stats = combined.reduceRegion({
    reducer: ee.Reducer.max(),  // a SINGLE triggering pixel is enough (Art. 9, no threshold)
    geometry: geom,
    scale: 30,          // native TMF resolution (Landsat)
    maxPixels: 1e9,
    bestEffort: true
  });

  var hasDefor = ee.Number(stats.get('defor_flag')).eq(1);
  var hasDegrad = ee.Number(stats.get('degrad_flag')).eq(1);
  var hasCoverage = ee.Number(stats.get('has_coverage')).eq(1);

  var verdict = ee.String(ee.Algorithms.If(
    hasCoverage.not(),
    'NEEDS_REVIEW_NO_TMF_COVERAGE',
    ee.Algorithms.If(
      hasDefor.or(hasDegrad),
      'NOT_COMPLIANT',
      'COMPLIANT'
    )
  ));

  return feature.set({
    verdict: verdict,
    tmf_deforestation_after_cutoff: hasDefor,
    tmf_degradation_after_cutoff: hasDegrad,
    tmf_has_coverage: hasCoverage,
    cutoff_year_used: CUTOFF_YEAR
  });
}

var evaluated = parcels.map(evaluateParcel);


// ---------------------------------------------------------------------------
// 4) OUTPUT: console + map
// ---------------------------------------------------------------------------

print('=== Result per parcel ===', evaluated);

// quick counters for the summary
print('Compliant (COMPLIANT):',
  evaluated.filter(ee.Filter.eq('verdict', 'COMPLIANT')).size());
print('Not compliant (NOT_COMPLIANT):',
  evaluated.filter(ee.Filter.eq('verdict', 'NOT_COMPLIANT')).size());
print('Need review (no TMF coverage):',
  evaluated.filter(ee.Filter.eq('verdict', 'NEEDS_REVIEW_NO_TMF_COVERAGE')).size());

var compliant = evaluated.filter(ee.Filter.eq('verdict', 'COMPLIANT'));
var notCompliant = evaluated.filter(ee.Filter.eq('verdict', 'NOT_COMPLIANT'));
var needsReview = evaluated.filter(ee.Filter.eq('verdict', 'NEEDS_REVIEW_NO_TMF_COVERAGE'));

Map.centerObject(parcels, 9);
Map.addLayer(gfc2020.selfMask(), {palette: ['4d9221']}, 'JRC forest 2020 (context)', false);
Map.addLayer(compliant, {color: '2e8b45'}, '✅ Compliant (no post-2020 deforestation/degradation)');
Map.addLayer(notCompliant, {color: 'c0392b'}, '⛔ NOT compliant (deforestation or degradation detected)');
Map.addLayer(needsReview, {color: 'e8a33d'}, '⚠️ No TMF coverage (review with another source)');


// ---------------------------------------------------------------------------
// 5) EXPORT RESULTS (optional: run this part when you want the file)
// ---------------------------------------------------------------------------
// A "RUN" button appears in the "Tasks" tab (top right) after running the
// script. You have to press it for the export to start.

Export.table.toDrive({
  collection: evaluated,
  description: 'EUDR_screening_results',
  fileFormat: 'GeoJSON'
});
