app_name = "openaec_bouw"
app_title = "OpenAEC Bouw"
app_publisher = "OpenAEC Studio BV"
app_description = "OpenAEC-inrichting van ERPNext voor de bouw: modules met stamgegevens die aan en uit kunnen"
app_email = "openaecstudio@gmail.com"
app_license = "agpl-3.0"

required_apps = ["frappe", "erpnext"]

# Installeren zet de standaardmodules; elke migratie (uitrol) vult aan met wat een nieuwe versie van een module brengt.
after_install = "openaec_bouw.profiel.na_installatie"
after_migrate = ["openaec_bouw.profiel.na_migratie"]
