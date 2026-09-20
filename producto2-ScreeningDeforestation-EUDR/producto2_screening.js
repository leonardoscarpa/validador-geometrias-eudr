// ============================================================================
// PRODUCTO 2 — EUDR Deforestation Screening
// Verifica cada parcela contra la fecha de corte del 31/12/2020.
//
// DECISIÓN DE DISEÑO CLAVE: JRC/GFC2020/V3 es una FOTO FIJA al 31/12/2020
// (un solo instante, banda "Map" = 1 si había bosque). Por sí sola NO puede
// decirnos si ese bosque se taló DESPUÉS — para eso usamos JRC Tropical
// Moist Forest (TMF) v1_2025, que sí tiene capas de "año de deforestación"
// y "año de degradación" pixel por pixel.
//
// PARA MADERA (el commodity de foco de este portfolio), el Art. 2 del
// Reglamento exige que la madera "haya sido cosechada sin inducir
// degradación forestal" después del corte — no alcanza con que no se haya
// deforestado. Por eso este script chequea DEFORESTACIÓN *y* DEGRADACIÓN,
// no solo una de las dos. La mayoría de las demos que vas a ver por ahí
// solo chequean deforestación.
//
// DESCALIFICACIÓN SIN UMBRAL (Art. 9): un solo píxel de deforestación o
// degradación post-2020 dentro del polígono descalifica TODA la parcela.
// No hay porcentaje de tolerancia.
//
// LIMITACIÓN CONOCIDA (documentada a propósito, no un bug escondido): TMF
// cubre el dominio de "bosque húmedo tropical". Misiones (selva paranaense)
// probablemente cae dentro; partes de Corrientes, más seca y al sur, pueden
// quedar FUERA del área mapeada por TMF. Cuando eso pasa, el script NO
// asume "apto" en silencio — devuelve "NEEDS_REVIEW_NO_TMF_COVERAGE" para
// que quede claro que ahí hace falta otra fuente de datos.
// ============================================================================


// ---------------------------------------------------------------------------
// 1) PARCELAS DE PRUEBA
// ---------------------------------------------------------------------------
// Tres parcelas sintéticas para probar el script: una en Misiones (selva,
// más probable que TMF la cubra), una en Corrientes (más al sur, posible
// que quede fuera del dominio de TMF), y una en Santiago del Estero (zona
// de desmonte activo bien documentado, para confirmar que el script SÍ
// detecta un caso real). Cajas agrandadas (~16x16 km y ~33x33 km) para que
// el resultado se vea mejor en el mapa y para aumentar la chance de
// capturar área efectivamente desmontada.

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
  // NUEVO (2do intento): caja en el departamento Copo, Santiago del Estero.
  // A diferencia de Anta (Salta) — probado antes, dio COMPLIANT — Copo
  // aparece citado explícitamente como una de las zonas "más afectadas" por
  // desmonte reciente (junto con Alberdi, Pellegrini y Moreno), y Santiago
  // del Estero es, en CADA informe anual 2021-2025 que encontré, la
  // provincia con más hectáreas desmontadas del país — más que Salta en
  // los años recientes, aunque Salta tenga un acumulado histórico mayor.
  // Caja de ~33x33 km centrada en el departamento para maximizar la chance
  // de capturar área realmente desmontada post-2020.
  ee.Feature(
    ee.Geometry.Polygon([[
      [-62.981, -25.656], [-62.681, -25.656],
      [-62.681, -25.956], [-62.981, -25.956], [-62.981, -25.656]
    ]]),
    {ParcelID: 'SDE-COPO-TEST-1', ProducerCountry: 'AR',
     CommonName: 'N/A (control negativo)', ScientificName: 'N/A'}
  )
]);

// --- PARA USAR TUS PROPIAS PARCELAS (el output.geojson del Producto 1) ---
// 1. Panel izquierdo > pestaña "Assets" > "NEW" > "Table upload" > subís el
//    .geojson. Tarda un par de minutos en procesarse.
// 2. Reemplazás el bloque de arriba por:
//      var parcels = ee.FeatureCollection('users/TU_USUARIO/TU_ASSET');
// 3. El resto del script no necesita ningún otro cambio, siempre que tus
//    propiedades usen los mismos nombres (ParcelID, ProducerCountry, etc.)
//    que ya vienen del Producto 1.


// ---------------------------------------------------------------------------
// 2) DATASETS
// ---------------------------------------------------------------------------

var CUTOFF_YEAR = 2020;

// Foto fija de bosque al 31/12/2020 — se usa solo como CONTEXTO visual, no
// para la decisión de apto/no apto (eso lo hace TMF, abajo).
var gfc2020 = ee.Image('JRC/GFC2020/V3').select('Map');

// TMF: año de deforestación y año de degradación, pixel por pixel.
// mosaic() junta los tiles continentales en una sola imagen continua.
var tmfDeforYear = ee.ImageCollection('projects/JRC/TMF/v1_2025/DeforestationYear').mosaic();
var tmfDegradYear = ee.ImageCollection('projects/JRC/TMF/v1_2025/DegradationYear').mosaic();

// Transition Map: se usa ÚNICAMENTE para saber si TMF tiene cobertura acá
// (cualquier categoría cuenta como "cobertura", incluso "no es bosque").
// A diferencia de DeforestationYear, que solo tiene datos donde SÍ hubo
// deforestación, la Transition Map clasifica todo lo que está dentro del
// dominio de TMF — por eso es la que sirve para detectar "sin datos".
var tmfTransition = ee.ImageCollection('projects/JRC/TMF/v1_2025/TransitionMap_Subtypes').mosaic();


// ---------------------------------------------------------------------------
// 3) EVALUACIÓN POR PARCELA
// ---------------------------------------------------------------------------

function evaluateParcel(feature) {
  var geom = feature.geometry();

  // .unmask(0): los píxeles nunca deforestados/degradados vienen "vacíos"
  // (sin dato) en TMF, no en 0. Los volvemos 0 explícito ANTES de comparar,
  // así reduceRegion no se confunde entre "nunca pasó" y "no hay dato".
  var deforAfterCutoff = tmfDeforYear.unmask(0).gt(CUTOFF_YEAR);
  var degradAfterCutoff = tmfDegradYear.unmask(0).gt(CUTOFF_YEAR);

  // .mask() de la Transition Map: 1 donde TMF tiene cualquier clasificación,
  // 0 donde el píxel está fuera de su dominio (bosque húmedo tropical).
  var hasCoverageImg = tmfTransition.mask();

  var combined = ee.Image.cat([
    deforAfterCutoff.rename('defor_flag'),
    degradAfterCutoff.rename('degrad_flag'),
    hasCoverageImg.rename('has_coverage')
  ]);

  var stats = combined.reduceRegion({
    reducer: ee.Reducer.max(),  // si UN SOLO píxel dispara, ya alcanza (Art. 9, sin umbral)
    geometry: geom,
    scale: 30,          // resolución nativa de TMF (Landsat)
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
// 4) SALIDA: consola + mapa
// ---------------------------------------------------------------------------

print('=== Resultado por parcela ===', evaluated);

// contadores rápidos para el resumen
print('Aptas (COMPLIANT):',
  evaluated.filter(ee.Filter.eq('verdict', 'COMPLIANT')).size());
print('NO aptas (NOT_COMPLIANT):',
  evaluated.filter(ee.Filter.eq('verdict', 'NOT_COMPLIANT')).size());
print('Necesitan revisión (sin cobertura TMF):',
  evaluated.filter(ee.Filter.eq('verdict', 'NEEDS_REVIEW_NO_TMF_COVERAGE')).size());

var compliant = evaluated.filter(ee.Filter.eq('verdict', 'COMPLIANT'));
var notCompliant = evaluated.filter(ee.Filter.eq('verdict', 'NOT_COMPLIANT'));
var needsReview = evaluated.filter(ee.Filter.eq('verdict', 'NEEDS_REVIEW_NO_TMF_COVERAGE'));

Map.centerObject(parcels, 9);
Map.addLayer(gfc2020.selfMask(), {palette: ['4d9221']}, 'JRC bosque 2020 (contexto)', false);
Map.addLayer(compliant, {color: '2e8b45'}, '✅ Apta (sin deforestación/degradación post-2020)');
Map.addLayer(notCompliant, {color: 'c0392b'}, '⛔ NO apta (deforestación o degradación detectada)');
Map.addLayer(needsReview, {color: 'e8a33d'}, '⚠️ Sin cobertura TMF — revisar con otra fuente');


// ---------------------------------------------------------------------------
// 5) EXPORTAR RESULTADOS (opcional — corré esta parte cuando quieras el archivo)
// ---------------------------------------------------------------------------
// Aparece un botón "RUN" en la pestaña "Tasks" (arriba a la derecha) después
// de correr el script — hay que apretarlo para que el export se dispare.

Export.table.toDrive({
  collection: evaluated,
  description: 'EUDR_screening_results',
  fileFormat: 'GeoJSON'
});
