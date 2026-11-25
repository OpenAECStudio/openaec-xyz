"""Doorloopt de ERPNext-installatiewizard en maakt de eerste beheerder.

Draait in de container vanuit de map `sites`, direct na `bench new-site`. Nederlandse inrichting: taal nl,
Europe/Amsterdam, EUR, standaard rekeningschema, boekjaar = dit kalenderjaar, zonder demodata.
"""

import os
import re

import frappe

TAAL, LAND, VALUTA, TIJDZONE = "nl", "Netherlands", "EUR", "Europe/Amsterdam"


def afkorting(bedrijf: str) -> str:
	letters = "".join(woord[0] for woord in re.findall(r"[A-Za-z0-9]+", bedrijf))
	return (letters or "YN").upper()[:5]


def wizard(bedrijf: str):
	if frappe.is_setup_complete():
		return
	from frappe.desk.page.setup_wizard.setup_wizard import initialize_system_settings_and_user, setup_complete
	from frappe.utils import getdate, today

	jaar = getdate(today()).year
	# De twee wizard-functies willen de taal verschillend: de eerste de code, de tweede de taalnaam.
	taalnaam = frappe.db.get_value("Language", TAAL, "language_name") or "Nederlands"
	initialize_system_settings_and_user(
		{"language": TAAL, "country": LAND, "currency": VALUTA, "time_zone": TIJDZONE},
		{},
	)
	setup_complete(
		{
			"language": taalnaam,
			"lang": TAAL,
			"country": LAND,
			"timezone": TIJDZONE,
			"currency": VALUTA,
			"company_name": bedrijf,
			"company_abbr": afkorting(bedrijf),
			"chart_of_accounts": "Standard",
			"fy_start_date": f"{jaar}-01-01",
			"fy_end_date": f"{jaar}-12-31",
			"setup_demo": 0,
		}
	)
	frappe.db.commit()
	frappe.clear_cache()
	if not frappe.is_setup_complete():
		raise SystemExit("De ERPNext-wizard is niet afgerond; zie de meldingen hierboven.")


def beheerder(email: str, naam: str, wachtwoord: str):
	"""Een eigen gebruiker met alle rollen, naast Administrator. Zonder e-mailadres gebeurt er niets."""
	if not email or frappe.db.exists("User", email):
		return
	from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to

	voornaam, _, achternaam = (naam or email.split("@")[0]).partition(" ")
	frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": voornaam,
			"last_name": achternaam,
			"language": TAAL,
			"time_zone": TIJDZONE,
			"send_welcome_email": 0,
			"new_password": wachtwoord,
		}
	).insert(ignore_permissions=True)
	add_all_roles_to(email)
	frappe.db.commit()


def main():
	frappe.init(os.environ.get("SITE_NAAM", "y-next.localhost"))
	frappe.connect()
	try:
		wizard(os.environ.get("BEDRIJF") or "Mijn Bedrijf")
		beheerder(
			(os.environ.get("BEHEERDER_EMAIL") or "").strip(),
			(os.environ.get("BEHEERDER_NAAM") or "").strip(),
			os.environ["ADMIN_PASSWORD"],
		)
	finally:
		frappe.destroy()


if __name__ == "__main__":
	main()
