app_name = "openaec_bouw"
app_title = "OpenAEC Bouw"
app_publisher = "OpenAEC Studio BV"
app_description = "OpenAEC-inrichting van ERPNext voor de bouw: modules met stamgegevens die aan en uit kunnen"
app_email = "openaecstudio@gmail.com"
app_license = "agpl-3.0"

# Frappe HR hoort er altijd bij: personeel, verlof en feestdagen bouwen erop (besluit 27 november 2026).
required_apps = ["frappe", "erpnext", "hrms"]

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
# Eerst de velden van de boekhouding (RGS-code, btw-code) en de bedrijfsinstellingen, dan het profiel, dan de btw-codes op wat het profiel zette.
after_install = ["openaec_bouw.boekhouding.na_migratie", "openaec_bouw.bedrijfsinstellingen.na_migratie", "openaec_bouw.profiel.na_installatie", "openaec_bouw.boekhouding.na_profiel", "openaec_bouw.personeel.na_migratie", "openaec_bouw.portaal.na_migratie"]
after_migrate = ["openaec_bouw.boekhouding.na_migratie", "openaec_bouw.bedrijfsinstellingen.na_migratie", "openaec_bouw.profiel.na_migratie", "openaec_bouw.boekhouding.na_profiel", "openaec_bouw.personeel.na_migratie", "openaec_bouw.portaal.na_migratie"]

# Op het bedrijf: de auditfile downloaden en het Nederlandse rekeningschema zetten.
doctype_js = {
	"Company": "public/js/company.js",
	"Sales Invoice": "public/js/sales_invoice.js",
	"Project": "public/js/project.js",
	"Portaaltoegang": "public/js/portaaltoegang.js",
}
# Op de lijsten: een bankafschrift (CAMT.053) inlezen, een UBL-factuur inlezen en een SEPA-betaalbestand maken.
doctype_list_js = {
	"Bank Transaction": "public/js/bank_transaction_list.js",
	"Purchase Invoice": "public/js/purchase_invoice_list.js",
}

# Een nieuwe gebruiker krijgt het rustige menu (module `rust`), als dat aan staat.
# Het deel van een factuur dat naar de G-rekening gaat, wordt bij het opslaan gevuld en bewaakt.
doc_events = {
	"User": {"before_insert": "openaec_bouw.profiel.nieuwe_gebruiker"},
	"Company": {"after_insert": "openaec_bouw.bedrijfsinstellingen.nieuw_bedrijf"},
	"Leave Application": {
		"validate": "openaec_bouw.personeel.aanvraag_controleren",
		"on_submit": "openaec_bouw.personeel.aanvraag_goedgekeurd",
		"on_cancel": "openaec_bouw.personeel.aanvraag_geannuleerd",
	},
	"Purchase Invoice": {"validate": "openaec_bouw.sepa.vul_g_bedrag"},
	"Sales Invoice": {"validate": "openaec_bouw.sepa.controleer_g_verkoop"},
}

# Verlof in uren: de verlofaanvraag slaat voor die soorten de controles in dagen over.
override_doctype_class = {"Leave Application": "openaec_bouw.verlofaanvraag.Verlofaanvraag"}

# Opbouw aan het eind van de maand, verval, contracten en cao-periodes bijwerken, kalenders een jaar vooruit.
scheduler_events = {"daily": ["openaec_bouw.personeel.dagelijks"]}

# Klantenportaal: /portaal (mijn projecten), /portaal/p/<project> na inloggen, /portaal/l/<sleutel> met een verborgen link.
website_route_rules = [
	{"from_route": "/portaal/p/<project>", "to_route": "portaal/project"},
	{"from_route": "/portaal/l/<sleutel>", "to_route": "portaal/project"},
]
