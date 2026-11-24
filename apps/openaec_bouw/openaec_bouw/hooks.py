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
after_install = "openaec_bouw.profiel.na_installatie"
after_migrate = ["openaec_bouw.profiel.na_migratie"]

# Een nieuwe gebruiker krijgt het rustige menu (module `rust`), als dat aan staat.
doc_events = {"User": {"before_insert": "openaec_bouw.profiel.nieuwe_gebruiker"}}
