"""Laadt de cao's uit `data/caos.json` als concept. Bestaande cao's en periodes worden niet overschreven: wat een
bedrijf heeft nagelopen of aangepast, blijft staan."""

import json

import frappe

from openaec_bouw.personeel import FEESTDAG_NAMEN


def laden():
	with open(frappe.get_app_path("openaec_bouw", "data", "caos.json")) as f:
		data = json.load(f)
	for cao in data["caos"]:
		if not frappe.db.exists("Cao", cao["cao_naam"]):
			frappe.get_doc({
				"doctype": "Cao", "cao_naam": cao["cao_naam"], "sector": cao.get("sector"), "partijen": cao.get("partijen"),
				"bron": cao.get("bron"), "werknemersgroepen": [{"groep": g} for g in cao["werknemersgroepen"]],
				"opmerking": "Uit de stamgegevens van OpenAEC Bouw. Na te lopen tegen de cao-tekst.",
			}).insert(ignore_permissions=True)
		for p in cao["periodes"]:
			if frappe.db.exists("Cao Periode", {"cao": cao["cao_naam"], "werknemersgroep": p["werknemersgroep"], "geldig_van": p["geldig_van"]}):
				continue
			regel = data["feestdagen"][p["feestdagen"]]
			frappe.get_doc({
				"doctype": "Cao Periode", "cao": cao["cao_naam"], "werknemersgroep": p["werknemersgroep"], "status": "Concept",
				"geldig_van": p["geldig_van"], "geldig_tot": p.get("geldig_tot"), "stilzwijgend_verlengen": p.get("stilzwijgend_verlengen", 0),
				"normuren_per_week": p["normuren_per_week"], "collectief_door_bedrijf": p.get("collectief_door_bedrijf", 0), "bron": cao.get("bron"),
				"verlofrechten": [
					{"verlofsoort": s, "uren_per_jaar": u, "verval": v} for s, u, v in p["verlofrechten"] if frappe.db.exists("Leave Type", s)
				],
				"feestdagen": [
					{"feestdag": d, "vrij": int(d in regel["vrij"]), "eens_per_vijf_jaar": int(d in regel["lustrum"])}
					for d in dict.fromkeys(FEESTDAG_NAMEN.values())
				],
				"loonafspraken": [{"datum": d, "percentage": pc, "bedrag": b, "omschrijving": o} for d, pc, b, o in p.get("loonafspraken", [])],
			}).insert(ignore_permissions=True)
