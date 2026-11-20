"""De lader van de OpenAEC-inrichting voor de bouw: modules met stamgegevens die per omgeving aan of uit kunnen.

Een module is een bestand in `modules/<id>.json` (zie README). Welke modules aan staan, staat als standaardwaarde
`openaec_bouw_modules` op de site. Wat de lader zette, staat in `Bouwprofiel Regel`.

Regels:
- **Alleen aanvullen:** een record dat er al staat, blijft zoals het is.
- **Wat de klant weghaalt, blijft weg:** een record met een regel maar zonder record zet de lader niet opnieuw.
- **Uitzetten** haalt weg wat de module zette, voor zover de klant het niet wijzigde en er niets aan hangt.

Voor `bench --site <site> execute openaec_bouw.profiel.<functie>` en (later) Beheer → Inrichting: `stand`, `pas_toe`
en `zet_module`.
"""

import json
from pathlib import Path

import frappe
from frappe import _

MAP = Path(__file__).parent / "modules"
AAN = "openaec_bouw_modules"
REGEL = "Bouwprofiel Regel"
# Bomen: DocType -> (veld van de bovenliggende groep).
BOMEN = {"Item Group": "parent_item_group", "Customer Group": "parent_customer_group", "Supplier Group": "parent_supplier_group"}
WORTEL = "@wortel"
BTW_SJABLONEN = ("Sales Taxes and Charges Template", "Purchase Taxes and Charges Template")


# --- modules ----------------------------------------------------------------------------------------------------


def modules() -> dict[str, dict]:
	"""Alle modules uit de app, op id."""
	uit = {}
	for bestand in sorted(MAP.glob("*.json")):
		module = json.loads(bestand.read_text(encoding="utf-8"))
		if module.get("id") != bestand.stem:
			frappe.throw(_("Module {0}: het id hoort de bestandsnaam te zijn").format(bestand.name))
		uit[module["id"]] = module
	return uit


def ingeschakeld() -> list[str] | None:
	"""De modules die aan staan; None als er nog nooit iets gekozen is."""
	waarde = frappe.db.get_default(AAN)
	return None if waarde is None else [m for m in json.loads(waarde) if m in modules()]


def _bewaar_aan(ids) -> None:
	frappe.db.set_default(AAN, json.dumps(sorted(set(ids))))


def _vereis_beheerder() -> None:
	frappe.only_for("System Manager")


@frappe.whitelist()
def stand() -> list[dict]:
	"""Per module: titel, omschrijving, aan of uit, en hoeveel records de lader zette."""
	_vereis_beheerder()
	gekozen = ingeschakeld() or []
	return [
		{
			"id": m["id"],
			"titel": m["titel"],
			"omschrijving": m.get("omschrijving"),
			"standaard": bool(m.get("standaard")),
			"versie": m.get("versie", 1),
			"aan": m["id"] in gekozen,
			"records": len(m["records"]),
			"gezet": frappe.db.count(REGEL, {"module": m["id"]}),
		}
		for m in modules().values()
	]


# --- toepassen --------------------------------------------------------------------------------------------------


def _vastleggen() -> None:
	if not frappe.flags.in_test:
		frappe.db.commit()


def _wortel(doctype: str) -> str:
	"""De wortel van een boom, welke naam (taal) hij ook heeft."""
	veld = BOMEN[doctype]
	wortels = [r.name for r in frappe.get_all(doctype, filters={"is_group": 1}, fields=["name", veld]) if not r.get(veld)]
	if not wortels:
		frappe.throw(_("{0} heeft geen wortel; doorloop eerst de wizard van ERPNext").format(doctype))
	return wortels[0]


def _onthoud(module: str, doctype: str, naam: str) -> None:
	frappe.get_doc(
		{"doctype": REGEL, "module": module, "soort": doctype, "record": naam, "gezet_op": str(frappe.db.get_value(doctype, naam, "modified"))}
	).insert(ignore_permissions=True)


def _al_gezet(module: str, doctype: str, naam: str) -> bool:
	return bool(frappe.db.exists(REGEL, {"module": module, "soort": doctype, "record": naam}))


def _zet(module: str, doctype: str, naam: str, velden: dict) -> bool:
	"""Maak het record als het er niet is en de lader het niet eerder zette. Geeft of er iets is aangemaakt."""
	if _al_gezet(module, doctype, naam) or frappe.db.exists(doctype, naam):
		return False
	doc = frappe.get_doc({"doctype": doctype, **velden})
	doc.insert(ignore_permissions=True)
	if doc.name != naam:
		frappe.throw(_("Module {0}: {1} {2} kreeg de naam {3}").format(module, doctype, naam, doc.name))
	_onthoud(module, doctype, naam)
	return True


def _gewoon(module: str, record: dict) -> int:
	doctype, velden = record["doctype"], dict(record.get("velden") or {})
	if doctype in BOMEN and velden.get(BOMEN[doctype]) == WORTEL:
		velden[BOMEN[doctype]] = _wortel(doctype)
	return int(_zet(module, doctype, record["naam"], velden))


def _belastinggroep(bedrijf: str) -> str | None:
	"""De groep waar de btw-rekeningen van dit bedrijf onder hangen: die van een bestaande btw-rekening, anders de
	groep met rekeningtype Tax."""
	blad = frappe.get_all("Account", filters={"company": bedrijf, "account_type": "Tax", "is_group": 0}, pluck="parent_account", limit=1)
	if blad:
		return blad[0]
	groep = frappe.get_all("Account", filters={"company": bedrijf, "account_type": "Tax", "is_group": 1}, pluck="name", limit=1)
	return groep[0] if groep else None


def _btw(module: str, record: dict) -> int:
	"""Per bedrijf: een btw-rekening en een sjabloon voor verkoop en inkoop met dat tarief. Een bedrijf zonder groep
	voor belastingen (eigen rekeningschema) wordt overgeslagen."""
	titel, tarief, tekst = record["naam"], float(record["tarief"]), record.get("omschrijving") or record["naam"]
	gezet = 0
	for bedrijf in frappe.get_all("Company", fields=["name", "abbr"]):
		groep = _belastinggroep(bedrijf.name)
		if not groep:
			continue
		rekening = f"{titel} - {bedrijf.abbr}"
		gezet += _zet(
			module,
			"Account",
			rekening,
			{"account_name": titel, "company": bedrijf.name, "parent_account": groep, "account_type": "Tax", "tax_rate": tarief},
		)
		if not frappe.db.exists("Account", rekening):
			continue  # de klant haalde de rekening weg: dan ook geen sjablonen
		for sjabloon in BTW_SJABLONEN:
			regel = {"charge_type": "On Net Total", "account_head": rekening, "description": tekst, "rate": tarief}
			if sjabloon.startswith("Purchase"):
				regel.update({"category": "Total", "add_deduct_tax": "Add"})
			gezet += _zet(module, sjabloon, rekening, {"title": titel, "company": bedrijf.name, "taxes": [regel]})
	return gezet


def _projectsjabloon(module: str, record: dict) -> int:
	"""Een Project Template met de fasen als sjabloontaken, na elkaar gepland (`dagen` per fase)."""
	naam = record["naam"]
	if _al_gezet(module, "Project Template", naam) or frappe.db.exists("Project Template", naam):
		return 0
	taken, begin = [], 0
	for fase in record["fasen"]:
		dagen = int(fase.get("dagen") or 10)
		taak = frappe.get_doc(
			{"doctype": "Task", "subject": fase["naam"], "is_template": 1, "start": begin, "duration": dagen}
		).insert(ignore_permissions=True)
		_onthoud(module, "Task", taak.name)
		taken.append({"task": taak.name, "subject": fase["naam"]})
		begin += dagen
	sjabloon = frappe.get_doc({"doctype": "Project Template", "__newname": naam, "tasks": taken})
	if record.get("projecttype") and frappe.db.exists("Project Type", record["projecttype"]):
		sjabloon.project_type = record["projecttype"]
	sjabloon.insert(ignore_permissions=True)
	_onthoud(module, "Project Template", sjabloon.name)
	return 1 + len(taken)


SOORTEN = {"btw": _btw, "projectsjabloon": _projectsjabloon}


def pas_toe(alleen=None) -> dict:
	"""Vul aan met de records van de modules die aan staan (of alleen de genoemde). Idempotent. Geeft per module het
	aantal records dat is aangemaakt."""
	if "erpnext" not in frappe.get_installed_apps() or not frappe.db.count("Company"):
		return {}  # ERPNext nog niet ingericht (de wizard maakt het bedrijf); na de wizard opnieuw
	alle, gekozen = modules(), ingeschakeld() or []
	ids = [alleen] if isinstance(alleen, str) else list(alleen or gekozen)
	uit = {}
	for id_ in ids:
		if id_ not in alle or id_ not in gekozen:
			continue
		uit[id_] = sum(SOORTEN.get(r.get("soort"), _gewoon)(id_, r) for r in alle[id_]["records"])
	_vastleggen()
	return uit


def _haal_weg(module: str) -> dict:
	"""Haal weg wat de module zette: alleen wat de klant niet wijzigde en waar niets aan hangt. De regels gaan altijd
	weg; opnieuw aanzetten vult dan weer aan."""
	weg, gebleven = 0, []
	# In omgekeerde volgorde: een sjabloon vóór zijn taken, een btw-sjabloon vóór zijn rekening.
	for regel in frappe.get_all(REGEL, filters={"module": module}, fields=["name", "soort", "record", "gezet_op"], order_by="creation desc, name desc"):
		gewijzigd = frappe.db.get_value(regel.soort, regel.record, "modified")
		if gewijzigd is not None:
			if str(gewijzigd) != regel.gezet_op:
				gebleven.append({"doctype": regel.soort, "naam": regel.record, "reden": "gewijzigd"})
			else:
				try:
					frappe.db.savepoint("bouwprofiel")
					frappe.delete_doc(regel.soort, regel.record, ignore_permissions=True)
					weg += 1
				except Exception:
					frappe.db.rollback(save_point="bouwprofiel")
					gebleven.append({"doctype": regel.soort, "naam": regel.record, "reden": "in gebruik"})
		frappe.delete_doc(REGEL, regel.name, ignore_permissions=True, force=True)
	return {"weg": weg, "gebleven": gebleven}


@frappe.whitelist(methods=["POST"])
def zet_module(module: str, aan: int | str | bool = 1) -> dict:
	"""Zet een module aan (vult aan) of uit (haalt weg wat ongewijzigd en ongebruikt is)."""
	_vereis_beheerder()
	if module not in modules():
		frappe.throw(_("Onbekende module {0}").format(module))
	gekozen = set(ingeschakeld() or [])
	wil_aan = frappe.utils.cint(aan) == 1
	if wil_aan:
		_bewaar_aan(gekozen | {module})
		uit = {"module": module, "aan": True, "gezet": pas_toe(module).get(module, 0)}
	else:
		_bewaar_aan(gekozen - {module})
		uit = {"module": module, "aan": False, **_haal_weg(module)}
	_vastleggen()
	return uit


# --- hooks ------------------------------------------------------------------------------------------------------


def na_installatie() -> None:
	"""De app installeren is het profiel willen: de standaardmodules aan, en toepassen als ERPNext al ingericht is."""
	if ingeschakeld() is None:
		_bewaar_aan(m["id"] for m in modules().values() if m.get("standaard"))
	pas_toe()


def na_migratie() -> None:
	"""Na elke uitrol: wat een nieuwe versie van een module brengt. Een fout hier mag de migratie niet tegenhouden."""
	try:
		if ingeschakeld() is None:
			_bewaar_aan(m["id"] for m in modules().values() if m.get("standaard"))
		pas_toe()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="OpenAEC Bouw: profiel toepassen mislukt")
