"""
Clasificación de riesgo país según el Anexo del Reglamento de Ejecución (UE)
2025/1093 de la Comisión, del 22/05/2025 (fuente: EUR-Lex, texto del Anexo
transcripto directamente, no un resumen de tercero).

Regla del propio reglamento (Art. 1):
  1. Los países listados en el Anexo son de riesgo BAJO o ALTO.
  2. Todo país NO listado mantiene el nivel ESTÁNDAR por defecto.

Por eso acá solo se transcriben las listas de BAJO y ALTO — el resto del
mundo es ESTÁNDAR por descarte, tal como lo exige el propio texto legal.
"""

LOW_RISK_COUNTRIES = {
    "Afghanistan", "Albania", "Algeria", "Andorra", "Antigua and Barbuda", "Armenia",
    "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
    "Belgium", "Bhutan", "Bosnia and Herzegovina", "Brunei Darussalam", "Bulgaria",
    "Burundi", "Cabo Verde", "Canada", "Central African Republic", "Chile", "China",
    "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia", "Denmark",
    "Djibouti", "Dominica", "Dominican Republic", "Egypt", "Estonia", "Eswatini", "Fiji",
    "Finland", "France", "Gabon", "Georgia", "Germany", "Ghana", "Greece", "Grenada",
    "Guyana", "Hungary", "Iceland", "India", "Iran (Islamic Republic of)", "Iraq",
    "Ireland", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati",
    "Kuwait", "Kyrgyzstan", "Lao People's Democratic Republic", "Latvia", "Lebanon",
    "Lesotho", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar",
    "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritius",
    "Micronesia (Federated States of)", "Monaco", "Mongolia", "Montenegro", "Morocco",
    "Nauru", "Nepal", "Netherlands (Kingdom of the)", "New Zealand", "North Macedonia",
    "Norway", "Oman", "Palau", "Palestine", "Papua New Guinea", "Philippines", "Poland",
    "Portugal", "Qatar", "Republic of Korea", "Republic of Moldova", "Romania", "Rwanda",
    "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa",
    "San Marino", "São Tomé and Príncipe", "Saudi Arabia", "Serbia", "Seychelles",
    "Singapore", "Slovakia", "Slovenia", "Solomon Island", "South Africa", "South Sudan",
    "Spain", "Sri Lanka", "Suriname", "Sweden", "Switzerland", "Syrian Arab Republic",
    "Tajikistan", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago",
    "Tunisia", "Türkiye", "Turkmenistan", "Tuvalu", "Ukraine", "United Arab Emirates",
    "United Kingdom of Great Britain and Northern Ireland", "United States of America",
    "Uruguay", "Uzbekistan", "Vanuatu", "Vietnam", "Yemen",
}

HIGH_RISK_COUNTRIES = {
    "Belarus", "Democratic People's Republic of Korea", "Myanmar", "Russian Federation",
}

# alias ISO-2 -> nombre oficial usado en el Anexo, para los países que de verdad
# vamos a usar en el Cono Sur / madera. Se puede ampliar si se necesita otro país.
ISO2_TO_ANNEX_NAME = {
    "AR": "Argentina", "BR": "Brazil", "PY": "Paraguay", "BO": "Bolivia (Plurinational State of)",
    "CL": "Chile", "UY": "Uruguay",
    # nota: Argentina/Brasil/Paraguay/Bolivia no figuran en el Anexo (ni bajo ni alto),
    # por eso no están en los sets de arriba — son ESTANDAR por descarte, según Art. 1(2)
    # del propio reglamento.
}

RISK_ORDER = {"Bajo": 0, "Estándar": 1, "Alto": 2}


def country_risk_tier(country_name_or_iso2):
    """Devuelve 'Bajo' | 'Estándar' | 'Alto' para un país, aceptando nombre
    completo (como en el Anexo) o código ISO-2 (para los del Cono Sur)."""
    name = ISO2_TO_ANNEX_NAME.get(country_name_or_iso2, country_name_or_iso2)
    if name in HIGH_RISK_COUNTRIES:
        return "Alto"
    if name in LOW_RISK_COUNTRIES:
        return "Bajo"
    return "Estándar"
