"""
Country risk classification according to the Annex of Commission Implementing
Regulation (EU) 2025/1093 of 22/05/2025 (source: EUR-Lex, Annex text
transcribed directly, not a third-party summary).

Rule of the regulation itself (Art. 1):
  1. Countries listed in the Annex are LOW or HIGH risk.
  2. Any country NOT listed keeps the STANDARD level by default.

That is why only the LOW and HIGH lists are transcribed here. The rest of
the world is STANDARD by omission, as the legal text itself requires.
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

# ISO-2 alias -> official name used in the Annex, for the countries we
# actually use in the Southern Cone / wood. It can be extended if another
# country is needed.
ISO2_TO_ANNEX_NAME = {
    "AR": "Argentina", "BR": "Brazil", "PY": "Paraguay", "BO": "Bolivia (Plurinational State of)",
    "CL": "Chile", "UY": "Uruguay",
    # note: Argentina/Brazil/Paraguay/Bolivia are not in the Annex (neither low nor
    # high), which is why they are not in the sets above. They are STANDARD by
    # omission, under Art. 1(2) of the regulation itself.
}

RISK_ORDER = {"Low": 0, "Standard": 1, "High": 2}


def country_risk_tier(country_name_or_iso2):
    """Returns 'Low' | 'Standard' | 'High' for a country, accepting the full
    name (as in the Annex) or an ISO-2 code (for the Southern Cone ones)."""
    name = ISO2_TO_ANNEX_NAME.get(country_name_or_iso2, country_name_or_iso2)
    if name in HIGH_RISK_COUNTRIES:
        return "High"
    if name in LOW_RISK_COUNTRIES:
        return "Low"
    return "Standard"
