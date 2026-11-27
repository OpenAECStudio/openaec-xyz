app_name = "z_next"
app_title = "Z Next"
app_publisher = "OpenAEC Foundation"
app_description = "Z-Next: projectadministratie, planning, offertes en bronkoppeling voor ERPNext"
app_email = ""

# De instellingen per bedrijf staan in OpenAEC Bouw (doctype Bedrijfsinstellingen), niet meer op het bedrijf.
required_apps = ["erpnext", "openaec_bouw"]

# Neemt bestaande custom doctypes met dezelfde naam over (custom=1, module Custom)
# zodat de model-sync ze bijwerkt in plaats van opnieuw aan te maken.
before_install = "z_next.install.before_install"

_ZNEXT_ROLES = ["Zapp Offertes", "Zapp Productie", "Zapp Superuser", "Zapp Werkplaats"]

fixtures = [
	{"dt": "Custom Field", "filters": [["module", "=", "Z Next"]]},
	{"dt": "Property Setter", "filters": [["module", "=", "Z Next"]]},
	{"dt": "Client Script", "filters": [["module", "=", "Z Next"]]},
	{"dt": "Server Script", "filters": [["module", "=", "Z Next"]]},
	{"dt": "Role", "filters": [["name", "in", _ZNEXT_ROLES]]},
	{"dt": "Custom DocPerm", "filters": [["role", "in", _ZNEXT_ROLES]]},
	{"dt": "Workspace", "filters": [["name", "in", ["Z-Next", "Zapp Dashboard", "Mijn Werkplek", "Werkplaats"]]]},
	{"dt": "Number Card", "filters": [["module", "=", "Z Next"]]},
	{"dt": "Dashboard Chart", "filters": [["module", "=", "Z Next"]]},
]
