// ============================================================================
// PRODUCT 4: EUDR dataset disagreement (multi-commodity comparison)
//
// For each synthetic test box this script measures, in hectares, what each
// satellite dataset says happened AFTER the EUDR cutoff (31/12/2020), and how
// much the datasets agree with each other. It produces NUMBERS, NOT VERDICTS:
// the point of the note is to show why one dataset's flag is not a compliance
// determination on its own.
//
// Datasets compared (all IDs confirmed by the probe run on 22/10/2026):
//   JRC GFC2020 V3     forest / non-forest snapshot at 31/12/2020 (EU baseline)
//   Hansen GFC 2025    tree cover loss per year (v1_13, loss year up to 2025)
//   JRC TMF v1_2025    deforestation year and degradation year (tropical moist)
//   RADD alerts        Sentinel-1 radar alerts, primary humid tropical forest only
//   FDP models         commodity probability (cocoa, coffee, palm), -24 to 24 deg
//
// KNOWN LIMITS (kept visible on purpose):
//   * The test boxes are SYNTHETIC. What is actually grown inside each box is
//     NOT verified. Boxes are labeled by the dominant regional commodity only.
//   * RADD only monitors primary humid tropical forest. Where it has no
//     baseline, "no RADD alerts" means "not monitored", NOT "no change".
//   * RADD 'Date' band is assumed to be YYDOY (e.g. 21001 = 1 Jan 2021). The
//     script exports the raw min/max so this can be checked, not assumed.
//   * Hansen "loss" is tree cover loss, not deforestation. It also fires on
//     plantation harvest and agroforestry. That is part of what we measure.
//   * Areas are computed per dataset at its native scale (10 m or 30 m).
//     Agreement counts are computed on a common 30 m grid.
// ============================================================================

var CUTOFF_YEAR = 2020;          // loss/defor/degrad year must be > 2020
var RADD_CUTOFF_DATE = 21000;    // YYDOY: anything above is on/after 1 Jan 2021
var BOX_SIZE_DEG = 0.2;          // ~22 km per side, ~48,000 ha

// ---------------------------------------------------------------------------
// 1) TEST BOXES (synthetic). radd_geo is the RADD region used for each box.
// ---------------------------------------------------------------------------
var sites = [
  {id: 'WOOD-MISIONES',   commodity: 'wood',    country: 'AR', lon: -54.60, lat: -26.40, radd_geo: 'sa',     fdp: ''},
  {id: 'SOY-PARA',        commodity: 'soy',     country: 'BR', lon: -54.75, lat:  -2.75, radd_geo: 'sa',     fdp: ''},
  {id: 'CATTLE-PARA',     commodity: 'cattle',  country: 'BR', lon: -52.00, lat:  -6.65, radd_geo: 'sa',     fdp: ''},
  {id: 'COFFEE-PERU',     commodity: 'coffee',  country: 'PE', lon: -77.00, lat:  -6.00, radd_geo: 'sa',     fdp: 'coffee'},
  {id: 'COCOA-CIV',       commodity: 'cocoa',   country: 'CI', lon:  -6.60, lat:   5.78, radd_geo: 'africa', fdp: 'cocoa'},
  {id: 'PALM-KALIMANTAN', commodity: 'oil palm', country: 'ID', lon: 111.62, lat:  -2.68, radd_geo: 'asia',   fdp: 'palm'}
];

var boxes = ee.FeatureCollection(sites.map(function (s) {
  var h = BOX_SIZE_DEG / 2;
  return ee.Feature(
    ee.Geometry.Rectangle([s.lon - h, s.lat - h, s.lon + h, s.lat + h], null, false),
    s);
}));

// ---------------------------------------------------------------------------
// 2) DATASETS
// ---------------------------------------------------------------------------
var gfc2020 = ee.Image('JRC/GFC2020/V3').select('Map');
var gfcForest = gfc2020.unmask(0).eq(1);

var hansen = ee.Image('UMD/hansen/global_forest_change_2025_v1_13');
var tc2000 = hansen.select('treecover2000');
var lossYear = hansen.select('lossyear');      // 0 = no loss, 1..25 = 2001..2025
var hansenLossAfterCutoff = lossYear.gt(CUTOFF_YEAR - 2000);

var tmfDefor = ee.ImageCollection('projects/JRC/TMF/v1_2025/DeforestationYear').mosaic();
var tmfDegrad = ee.ImageCollection('projects/JRC/TMF/v1_2025/DegradationYear').mosaic();
var tmfFlag = tmfDefor.unmask(0).gt(CUTOFF_YEAR).or(tmfDegrad.unmask(0).gt(CUTOFF_YEAR));

var radd = ee.ImageCollection('projects/radar-wur/raddalert/v1');
var raddBaseline = radd.filter(ee.Filter.eq('layer', 'forest_baseline_2019')).mosaic().select([0]);
var raddCovered = raddBaseline.unmask(0).gt(0);

// Latest cumulative alert image of one RADD region (ids look like 'sa_20250105').
function latestRaddAlerts(geo) {
  return ee.Image(radd.filter(ee.Filter.eq('layer', 'alerts'))
    .filter(ee.Filter.eq('geography', geo))
    .sort('system:index', false)
    .first());
}

function fdpProbability(commodity) {
  return ee.ImageCollection('projects/forestdatapartnership/assets/' + commodity + '/model_2026a')
    .filterDate('2024-01-01', '2025-01-01').mosaic().select('probability');
}
var fdpCocoa = fdpProbability('cocoa');
var fdpCoffee = fdpProbability('coffee');
var fdpPalm = fdpProbability('palm');

// ---------------------------------------------------------------------------
// 3) HELPERS
// ---------------------------------------------------------------------------
function num(v) { return ee.Number(ee.Algorithms.If(v, v, 0)); }

// hectares where `flag` is true, inside `geom`, measured at `scale` meters
function haOf(flag, geom, scale) {
  var v = ee.Image.pixelArea().divide(10000).updateMask(flag)
    .reduceRegion({reducer: ee.Reducer.sum(), geometry: geom, scale: scale,
                   maxPixels: 1e10, tileScale: 4}).get('area');
  return num(v).multiply(100).round().divide(100);
}

// ---------------------------------------------------------------------------
// 4) PER-BOX MEASUREMENTS
// ---------------------------------------------------------------------------
var measured = boxes.map(function (f) {
  var geom = f.geometry();
  var geo = f.get('radd_geo');
  var alerts = latestRaddAlerts(geo);
  var alertDate = alerts.select('Date');
  var alertVal = alerts.select('Alert');

  var raddAny = alertVal.gte(2).and(alertDate.gt(RADD_CUTOFF_DATE)).unmask(0);
  var raddConfirmed = alertVal.eq(3).and(alertDate.gt(RADD_CUTOFF_DATE)).unmask(0);

  var h10 = hansenLossAfterCutoff.and(tc2000.gte(10));
  var h30 = hansenLossAfterCutoff.and(tc2000.gte(30));

  // agreement on a common 30 m grid: how many of Hansen(30%), TMF, RADD flag a pixel
  var agree = h30.unmask(0).add(tmfFlag).add(raddAny);
  var areaHa = ee.Image.pixelArea().divide(10000);
  var agreeBands = ee.Image.cat([
    areaHa.updateMask(agree.eq(1)).rename('a1'),
    areaHa.updateMask(agree.eq(2)).rename('a2'),
    areaHa.updateMask(agree.eq(3)).rename('a3')
  ]).reduceRegion({reducer: ee.Reducer.sum(), geometry: geom, scale: 30,
                   maxPixels: 1e10, tileScale: 4});

  var dateStats = alertDate.updateMask(alertDate.gt(0)).reduceRegion({
    reducer: ee.Reducer.minMax(), geometry: geom, scale: 30,
    maxPixels: 1e10, tileScale: 4});

  var fdpName = ee.String(f.get('fdp'));
  var fdpImg = ee.Image(ee.Algorithms.If(fdpName.equals('cocoa'), fdpCocoa,
    ee.Algorithms.If(fdpName.equals('coffee'), fdpCoffee,
      ee.Algorithms.If(fdpName.equals('palm'), fdpPalm, ee.Image(0)))));
  var lat = ee.Number(geom.centroid(1).coordinates().get(1));
  var fdpApplicable = fdpName.length().gt(0).and(lat.abs().lte(24));

  return f.set({
    box_ha: num(geom.area(1)).divide(10000).round(),
    // baselines
    gfc2020_forest_ha: haOf(gfcForest, geom, 10),
    radd_monitored_primary_forest_ha: haOf(raddCovered, geom, 10),
    // post-cutoff change, per dataset
    hansen_loss_post2020_tc10_ha: haOf(h10, geom, 30),
    hansen_loss_post2020_tc30_ha: haOf(h30, geom, 30),
    hansen_loss_post2020_inside_gfc2020_forest_ha: haOf(h30.and(gfcForest), geom, 30),
    tmf_deforestation_post2020_ha: haOf(tmfDefor.unmask(0).gt(CUTOFF_YEAR), geom, 30),
    tmf_degradation_post2020_ha: haOf(tmfDegrad.unmask(0).gt(CUTOFF_YEAR), geom, 30),
    radd_alerts_post2020_any_ha: haOf(raddAny, geom, 10),
    radd_alerts_post2020_confirmed_ha: haOf(raddConfirmed, geom, 10),
    // agreement (Hansen 30%, TMF, RADD) on a 30 m grid
    flagged_by_1_dataset_ha: num(agreeBands.get('a1')),
    flagged_by_2_datasets_ha: num(agreeBands.get('a2')),
    flagged_by_3_datasets_ha: num(agreeBands.get('a3')),
    // raw RADD date range, to verify the YYDOY assumption
    radd_date_min_raw: dateStats.get('Date_min'),
    radd_date_max_raw: dateStats.get('Date_max'),
    // commodity model context (only where the model applies)
    fdp_model_applicable: fdpApplicable,
    fdp_prob_gt_0_5_ha: ee.Number(ee.Algorithms.If(fdpApplicable,
      haOf(fdpImg.gt(0.5), geom, 10), -1))
  });
});

print('=== Product 4: dataset comparison per box (hectares) ===', measured);

// compact, copyable output
measured.evaluate(function (fc) {
  print('RESULTS: ' + JSON.stringify(fc.features.map(function (f) { return f.properties; })));
});

// ---------------------------------------------------------------------------
// 5) MAP (layers start hidden except the boxes; switch them on in the Layers menu)
// ---------------------------------------------------------------------------
Map.setCenter(-54.60, -26.40, 9);
Map.addLayer(boxes.style({color: 'ffffff', fillColor: '00000000', width: 2}), {}, 'Test boxes');
Map.addLayer(gfcForest.selfMask(), {palette: ['4d9221']}, 'JRC GFC2020 forest', false);
Map.addLayer(hansenLossAfterCutoff.and(tc2000.gte(30)).selfMask(), {palette: ['e67e22']}, 'Hansen loss after 2020 (tc>=30)', false);
Map.addLayer(tmfFlag.selfMask(), {palette: ['c0392b']}, 'TMF deforestation or degradation after 2020', false);
Map.addLayer(latestRaddAlerts('sa').select('Date').gt(RADD_CUTOFF_DATE).selfMask(), {palette: ['8e44ad']}, 'RADD alerts after 2020 (South America)', false);

// ---------------------------------------------------------------------------
// 6) EXPORT (press RUN in the Tasks tab)
// ---------------------------------------------------------------------------
Export.table.toDrive({
  collection: measured,
  description: 'EUDR_product4_dataset_comparison',
  fileFormat: 'CSV',
  selectors: ['id', 'commodity', 'country', 'radd_geo', 'box_ha',
    'gfc2020_forest_ha', 'radd_monitored_primary_forest_ha',
    'hansen_loss_post2020_tc10_ha', 'hansen_loss_post2020_tc30_ha',
    'hansen_loss_post2020_inside_gfc2020_forest_ha',
    'tmf_deforestation_post2020_ha', 'tmf_degradation_post2020_ha',
    'radd_alerts_post2020_any_ha', 'radd_alerts_post2020_confirmed_ha',
    'flagged_by_1_dataset_ha', 'flagged_by_2_datasets_ha', 'flagged_by_3_datasets_ha',
    'radd_date_min_raw', 'radd_date_max_raw', 'fdp_model_applicable', 'fdp_prob_gt_0_5_ha']
});
