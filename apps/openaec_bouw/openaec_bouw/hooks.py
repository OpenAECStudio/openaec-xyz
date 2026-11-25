app_name = "openaec_bouw"
app_title = "OpenAEC Bouw"
app_publisher = "OpenAEC Studio BV"
app_description = "OpenAEC-inrichting van ERPNext voor de bouw: modules met stamgegevens die aan en uit kunnen"
app_email = "openaecstudio@gmail.com"
app_license = "agpl-3.0"

required_apps = ["frappe", "erpnext"]

# De tegel op het startscherm: opent de werkruimte Bouwbedrijf met de zijbalk van de module.
add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/openaec_bouw/images/bouwbedrijf.svg",
		"title": "Bouwbedrijf",
		"route": "/desk/bouwbedrijf",
		"has_permission": "openaec_bouw.start.mag_zien",
		"sequence_id": 0,
	}
]

# Installeren zet de standaardmodules; elke migratie (uitrol) vult aan met wat een nieuwe versie van een module brengt.
# Eerst de velden van de boekhouding (RGS-code, btw-code), dan het profiel, dan de btw-codes op wat het profiel zette.
after_install = ["openaec_bouw.boekhouding.na_migratie", "openaec_bouw.profiel.na_installatie", "openaec_bouw.boekhouding.na_profiel"]
after_migrate = ["openaec_bouw.boekhouding.na_migratie", "openaec_bouw.profiel.na_migratie", "openaec_bouw.boekhouding.na_profiel"]

# Op het bedrijf: de auditfile downloaden en het Nederlandse rekeningschema zetten.
doctype_js = {"Company": "public/js/company.js", "Sales Invoice": "public/js/sales_invoice.js"}
# Op de lijsten: een bankafschrift (CAMT.053) inlezen, een UBL-factuur inlezen en een SEPA-betaalbestand maken.
doctype_list_js = {
	"Bank Transaction": "public/js/bank_transaction_list.js",
	"Purchase Invoice": "public/js/purchase_invoice_list.js",
}

# Een nieuwe gebruiker krijgt het rustige menu (module `rust`), als dat aan staat.
# Het deel van een factuur dat naar de G-rekening gaat, wordt bij het opslaan gevuld en bewaakt.
doc_events = {
	"User": {"before_insert": "openaec_bouw.profiel.nieuwe_gebruiker"},
	"Purchase Invoice": {"validate": "openaec_bouw.sepa.vul_g_bedrag"},
	"Sales Invoice": {"validate": "openaec_bouw.sepa.controleer_g_verkoop"},
}
