// ============================================================================
// PRODUCT 4: side-by-side image panels (one set per test box)
//
// Only the two boxes used in the write-up, four panels each = 8 images:
//   hansen  Hansen tree cover loss after 2020, tree cover >= 30% (orange)
//   tmf     JRC TMF deforestation or degradation after 2020 (red)
//   radd    RADD: pale purple = monitored primary forest, dark purple = alerts
//   agree   how many of Hansen, TMF and RADD flag each pixel (1, 2 or 3)
//
// HOW TO USE: press Run, then click each of the 8 links in the Console and
// save the PNG with the exact name shown (e.g. SOY-PARA_hansen.png).
//
// These are SYNTHETIC boxes. Nothing here is a compliance verdict.
// ============================================================================

var CUTOFF_YEAR = 2020;
var RADD_CUTOFF_DATE = 21000;   // assumed YYDOY, see the note
var BOX_SIZE_DEG = 0.2;
var PX = 900;                   // thumbnail width in pixels (~25 m per pixel)

var sites = [
  {id: 'WOOD-MISIONES', lon: -54.60, lat: -26.40, geo: 'sa'},
  {id: 'SOY-PARA',      lon: -54.75, lat:  -2.75, geo: 'sa'}
];

// ---- datasets (same definitions as product4_comparison.js) ------------------
var gfcForest = ee.Image('JRC/GFC2020/V3').select('Map').unmask(0).eq(1);
var hansen = ee.Image('UMD/hansen/global_forest_change_2025_v1_13');
var h30 = hansen.select('lossyear').gt(CUTOFF_YEAR - 2000)
  .and(hansen.select('treecover2000').gte(30)).unmask(0);
var tmfDefor = ee.ImageCollection('projects/JRC/TMF/v1_2025/DeforestationYear').mosaic();
var tmfDegrad = ee.ImageCollection('projects/JRC/TMF/v1_2025/DegradationYear').mosaic();
var tmfFlag = tmfDefor.unmask(0).gt(CUTOFF_YEAR).or(tmfDegrad.unmask(0).gt(CUTOFF_YEAR));
var radd = ee.ImageCollection('projects/radar-wur/raddalert/v1');
var raddCovered = radd.filter(ee.Filter.eq('layer', 'forest_baseline_2019'))
  .mosaic().select([0]).unmask(0).gt(0);

function latestRaddAlerts(geo) {
  return ee.Image(radd.filter(ee.Filter.eq('layer', 'alerts'))
    .filter(ee.Filter.eq('geography', geo)).sort('system:index', false).first());
}

// light gray canvas so "no data / no flag" is visible and consistent
var canvas = ee.Image.constant(1).visualize({palette: ['f2f2f2'], min: 0, max: 1});

function over(maskImg, color) {
  return maskImg.selfMask().visualize({palette: [color], min: 0, max: 1});
}

function panel(name, siteId, image, geom) {
  image.getThumbURL({dimensions: PX, region: geom, format: 'png'}, function (url, err) {
    if (err || !url) { print(siteId + '_' + name + ': ERROR ' + err); return; }
    print(siteId + '_' + name + '.png', ui.Label(siteId + '_' + name + '.png', {}, url));
  });
}

sites.forEach(function (s) {
  var h = BOX_SIZE_DEG / 2;
  var geom = ee.Geometry.Rectangle([s.lon - h, s.lat - h, s.lon + h, s.lat + h], null, false);

  var alerts = latestRaddAlerts(s.geo);
  var raddAny = alerts.select('Alert').gte(2)
    .and(alerts.select('Date').gt(RADD_CUTOFF_DATE)).unmask(0);
  var agree = h30.add(tmfFlag).add(raddAny);

  // four panels per box
  panel('hansen', s.id, canvas.blend(over(h30, 'e67e22')), geom);
  panel('tmf', s.id, canvas.blend(over(tmfFlag, 'c0392b')), geom);
  panel('radd', s.id, canvas
    .blend(over(raddCovered, 'd7c4e8'))
    .blend(over(raddAny, '5b2c83')), geom);

  // agreement: 1 = yellow, 2 = orange-red, 3 = dark red
  panel('agree', s.id, canvas.blend(
    agree.updateMask(agree.gt(0)).visualize({min: 1, max: 3, palette: ['f1c40f', 'e67e22', '7b1d1d']})), geom);
});

Map.setCenter(-54.60, -26.40, 9);
print('Click each link below and save the PNG with the exact name shown.');
