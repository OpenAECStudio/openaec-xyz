import json
import os

import frappe

MODULE = "Z Next"


def app_doctypes():
	"""Namen van alle doctypes die deze app levert."""
	root = frappe.get_app_path("z_next", "z_next", "doctype")
	names = []
	for folder in sorted(os.listdir(root)):
		path = os.path.join(root, folder, folder + ".json")
		if os.path.exists(path):
			with open(path, encoding="utf-8") as f:
				names.append(json.load(f)["name"])
	return names


def before_install():
	"""Zet bestaande custom doctypes om naar standaard-doctypes van module Z Next.

	Tabellen en records blijven staan; alleen de metadata in tabDocType wordt
	omgezet, waarna de model-sync de velden uit de app-JSON overneemt.
	"""
	# Module Def "Z Next" wordt direct hierna door install_app aangemaakt; set_value valideert geen links.
	claimed = []
	for name in app_doctypes():
		if frappe.db.get_value("DocType", name, "custom"):
			frappe.db.set_value("DocType", name, {"custom": 0, "module": MODULE}, update_modified=False)
			claimed.append(name)

	if claimed:
		print(f"Z Next: {len(claimed)} bestaande custom doctypes overgenomen")
