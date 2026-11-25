"""De Nederlandse laag op de boekhouding van ERPNext.

- Elke grootboekrekening krijgt een **RGS-code** (veld `rgs_code` op Account). Rapporten en de auditfile lezen die
  code, niet de naam van de rekening: een klant mag zijn schema dus aanpassen.
- Elk btw-sjabloon krijgt een **btw-code** (veld `btw_code`), die zegt in welke rubriek van de aangifte het hoort.
- Een nieuw bedrijf krijgt het eigen rekeningschema `data/rekeningschema.json` (Nederlands, voor een bouwbedrijf),
  met de standaardrekeningen van het bedrijf erbij.

De RGS-codes zijn een voorstel op het niveau waarop ze zeker zijn; een boekhouder loopt ze na.
"""

import json
import os

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Verkoop en inkoop: code → rubriek van de aangifte omzetbelasting.
BTW_CODES = {
	"V21": "1a",
	"V9": "1b",
	"VOV": "1c",
	"V0": "1e",
	"VVERL": "1e",
	"VEXP": "3a",
	"VEU": "3b",
	"I21": "5b",
	"I9": "5b",
	"I0": "5b",
	"IVERL": "2a",
	"IBUI": "4a",
	"IEU": "4b",
}
BTW_TEKSTEN = {
	"V21": "Verkoop 21%",
	"V9": "Verkoop 9%",
	"VOV": "Verkoop overig tarief",
	"V0": "Verkoop 0% of vrijgesteld",
	"VVERL": "Verkoop, btw verlegd naar de afnemer",
	"VEXP": "Verkoop buiten de EU",
	"VEU": "Verkoop binnen de EU",
	"I21": "Inkoop 21%",
	"I9": "Inkoop 9%",
	"I0": "Inkoop 0% of vrijgesteld",
	"IVERL": "Inkoop, btw naar ons verlegd",
	"IBUI": "Inkoop buiten de EU",
	"IEU": "Inkoop binnen de EU",
}

# Voorstel voor een rekening zonder RGS-code, eerst op rekeningtype en dan op hoofdtype.
RGS_PER_TYPE = {
	"Receivable": "BVorDeb",
	"Payable": "BSchCre",
	"Bank": "BLimBan",
	"Cash": "BLimKas",
	"Tax": "BSchBep",
	"Stock": "BVrd",
	"Fixed Asset": "BMva",
	"Accumulated Depreciation": "BMva",
	"Capital Work in Progress": "BMva",
	"Depreciation": "WAfs",
	"Cost of Goods Sold": "WKpr",
	"Stock Adjustment": "WKpr",
	"Round Off": "WBedAlk",
	"Stock Received But Not Billed": "BSch",
}
RGS_PER_HOOFDTYPE = {"Asset": "BVor", "Liability": "BSch", "Equity": "BEiv", "Income": "WOmz", "Expense": "WBed"}


def _velden() -> dict:
	def code(soort: str) -> dict:
		keuzes = [c for c in BTW_CODES if c.startswith(soort)]
		return {
			"fieldname": "btw_code",
			"label": "Btw-code",
			"fieldtype": "Select",
			"options": "\n" + "\n".join(keuzes),
			"insert_after": "company",
			"description": "Bepaalt de rubriek van de btw-aangifte: " + "; ".join(f"{c} = {BTW_TEKSTEN[c]}" for c in keuzes),
		}

	return {
		"Account": [
			{
				"fieldname": "rgs_code",
				"label": "RGS-code",
				"fieldtype": "Data",
				"insert_after": "account_type",
				"description": "Code uit het Referentie GrootboekSchema. Rapporten en de auditfile lezen deze code.",
			}
		],
		"Sales Taxes and Charges Template": [code("V")],
		"Purchase Taxes and Charges Template": [code("I")],
		"Company": [
			{
				"fieldname": "kvk_nummer",
				"label": "KvK-nummer",
				"fieldtype": "Data",
				"insert_after": "tax_id",
				"description": "Acht cijfers. Staat op de UBL-factuur.",
			},
			{
				"fieldname": "g_rekening",
				"label": "G-rekening",
				"fieldtype": "Link",
				"options": "Bank Account",
				"insert_after": "default_bank_account",
				"description": "De eigen geblokkeerde rekening; staat op verkoopfacturen met een G-bedrag.",
			},
		],
		"Supplier": [
			{
				"fieldname": "g_rekening_iban",
				"label": "IBAN G-rekening",
				"fieldtype": "Data",
				"insert_after": "tax_id",
				"description": "De geblokkeerde rekening van de onderaannemer (Wet ketenaansprakelijkheid).",
			},
			{
				"fieldname": "g_percentage",
				"label": "Naar de G-rekening (%)",
				"fieldtype": "Percent",
				"insert_after": "g_rekening_iban",
				"description": "Afgesproken deel van het factuurbedrag zonder btw. Vult het G-bedrag op een nieuwe inkoopfactuur.",
			},
		],
		"Purchase Invoice": [
			{
				"fieldname": "g_bedrag",
				"label": "Naar de G-rekening",
				"fieldtype": "Currency",
				"options": "currency",
				"insert_after": "bill_date",
				"allow_on_submit": 1,
				"description": "Dit deel gaat in het betaalbestand naar de G-rekening van de leverancier.",
			},
			{
				"fieldname": "sepa_bestand",
				"label": "In betaalbestand",
				"fieldtype": "Data",
				"insert_after": "g_bedrag",
				"read_only": 1,
				"no_copy": 1,
				"allow_on_submit": 1,
			},
		],
		"Project": [
			{
				"fieldname": "aanneemsom",
				"label": "Aanneemsom",
				"fieldtype": "Currency",
				"insert_after": "estimated_costing",
				"description": "De opdrachtsom zonder btw, met het opgedragen meerwerk erbij. Basis voor het onderhanden werk.",
			}
		],
		"Item": [
			{
				"fieldname": "keurmerk",
				"label": "Keurmerk hout",
				"fieldtype": "Select",
				"options": "\nFSC 100%\nFSC Mix\nPEFC\nGeen",
				"insert_after": "country_of_origin",
			}
		],
		"Batch": [
			{
				"fieldname": "herkomst_land",
				"label": "Land van herkomst",
				"fieldtype": "Link",
				"options": "Country",
				"insert_after": "supplier",
				"description": "Bij hout: waar het gekapt is. Een levering moet naar de herkomst te herleiden zijn.",
			},
			{"fieldname": "herkomst_gebied", "label": "Gebied of concessie", "fieldtype": "Data", "insert_after": "herkomst_land"},
		],
		"Sales Invoice": [
			{
				"fieldname": "g_bedrag",
				"label": "Naar de G-rekening",
				"fieldtype": "Currency",
				"options": "currency",
				"insert_after": "due_date",
				"allow_on_submit": 1,
				"description": "Dit deel betaalt de opdrachtgever op de G-rekening van het bedrijf.",
			}
		],
	}


def schema() -> dict:
	with open(os.path.join(os.path.dirname(__file__), "data", "rekeningschema.json"), encoding="utf-8") as f:
		return json.load(f)


def _boom(rekeningen: list) -> dict:
	"""De platte lijst als de geneste boom die `create_charts` van ERPNext verwacht."""
	knopen, boom = {}, {}
	for nummer, naam, ouder, soort, _rgs in rekeningen:
		knoop = {}
		if ouder is None:
			knoop["root_type"] = soort
		else:
			knoop["account_number"] = nummer
			if soort:
				knoop["account_type"] = soort
		knopen[nummer] = knoop
		(boom if ouder is None else knopen[ouder])[naam] = knoop
	for nummer, _naam, _ouder, _soort, _rgs in rekeningen:
		if any(isinstance(v, dict) for v in knopen[nummer].values()):
			knopen[nummer]["is_group"] = 1
	return boom


def rgs_voorstel(rekeningtype: str | None, hoofdtype: str | None) -> str | None:
	return RGS_PER_TYPE.get(rekeningtype or "") or RGS_PER_HOOFDTYPE.get(hoofdtype or "")


def vul_rgs_aan(bedrijf: str | None = None) -> int:
	"""Geeft elke rekening zonder RGS-code een voorstel. Wat er al staat (ook van de klant) blijft staan."""
	filters = {"rgs_code": ("is", "not set")}
	if bedrijf:
		filters["company"] = bedrijf
	gezet = 0
	for r in frappe.get_all("Account", filters=filters, fields=["name", "account_type", "root_type"]):
		code = rgs_voorstel(r.account_type, r.root_type)
		if code:
			frappe.db.set_value("Account", r.name, "rgs_code", code, update_modified=False)
			gezet += 1
	return gezet


def heeft_boekingen(bedrijf: str) -> bool:
	return bool(frappe.db.exists("GL Entry", {"company": bedrijf}))


@frappe.whitelist(methods=["POST"])
def zet_rekeningschema(bedrijf: str) -> dict:
	"""Vervangt het rekeningschema van een bedrijf zonder boekingen door het Nederlandse schema van OpenAEC Bouw, zet de
	standaardrekeningen van het bedrijf en past daarna de modules opnieuw toe (de btw-sjablonen hangen aan het schema).
	Een bedrijf waar al op geboekt is, wordt geweigerd: een schema wisselen kan dan niet meer."""
	frappe.only_for("System Manager")
	from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts
	from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import unset_existing_data

	from openaec_bouw import profiel

	if not frappe.db.exists("Company", bedrijf):
		frappe.throw(_("Onbekend bedrijf {0}").format(bedrijf))
	if heeft_boekingen(bedrijf):
		frappe.throw(_("Op {0} is al geboekt; het rekeningschema kan niet meer vervangen worden.").format(bedrijf))
	zorg_voor_velden()
	gegevens = schema()

	# Wat de lader voor dit bedrijf aan rekeningen en btw-sjablonen zette, verdwijnt mee: vergeten, zodat het terugkomt.
	afkorting = frappe.db.get_value("Company", bedrijf, "abbr")
	frappe.db.delete(
		profiel.REGEL,
		{
			"soort": ("in", ["Account", "Sales Taxes and Charges Template", "Purchase Taxes and Charges Template"]),
			"record": ("like", f"% - {afkorting}"),
		},
	)
	unset_existing_data(bedrijf)
	frappe.local.flags.ignore_root_company_validation = True
	create_charts(bedrijf, custom_chart=_boom(gegevens["rekeningen"]))
	return _werk_schema_af(bedrijf, gegevens)


@frappe.whitelist(methods=["POST"])
def neem_schema_over(bedrijf: str) -> dict:
	"""Voor een dochterbedrijf in een groep. ERPNext kopieert het rekeningschema van het moederbedrijf zodra een bedrijf
	met een moeder wordt aangemaakt, maar zonder de RGS-codes, de standaardrekeningen en de btw-sjablonen. Dit zet die
	erbij, als het moederbedrijf het Nederlandse schema van OpenAEC Bouw heeft. Er wordt niets vervangen."""
	frappe.only_for("System Manager")
	from openaec_bouw import profiel

	moeder = frappe.db.get_value("Company", bedrijf, "parent_company")
	gegevens = schema()
	if not moeder or frappe.db.get_value("Company", moeder, "chart_of_accounts") != gegevens["naam"]:
		frappe.throw(_("{0} heeft geen moederbedrijf met het Nederlandse rekeningschema.").format(bedrijf))
	zorg_voor_velden()
	afkorting = frappe.db.get_value("Company", bedrijf, "abbr")
	frappe.db.delete(
		profiel.REGEL,
		{
			"soort": ("in", ["Account", "Sales Taxes and Charges Template", "Purchase Taxes and Charges Template"]),
			"record": ("like", f"% - {afkorting}"),
		},
	)
	_ruim_landinrichting_op(bedrijf)
	return _werk_schema_af(bedrijf, gegevens)


def _ruim_landinrichting_op(bedrijf: str) -> None:
	"""ERPNext zet bij een nieuw Nederlands bedrijf eigen btw-rekeningen en -sjablonen neer (VAT 21%, VAT 6%). Die
	staan buiten ons schema en dubbelen onze sjablonen; zolang er niet op geboekt is, gaan ze eruit."""
	if heeft_boekingen(bedrijf):
		return
	vreemd = frappe.get_all("Account", filters={"company": bedrijf, "is_group": 0, "account_type": "Tax", "account_number": ("is", "not set")}, pluck="name")
	if not vreemd:
		return
	for kind, sjabloon in (("Sales Taxes and Charges", "Sales Taxes and Charges Template"), ("Purchase Taxes and Charges", "Purchase Taxes and Charges Template"), ("Item Tax Template Detail", "Item Tax Template")):
		veld = "tax_type" if kind == "Item Tax Template Detail" else "account_head"
		for naam in set(frappe.get_all(kind, filters={veld: ("in", vreemd), "parenttype": sjabloon}, pluck="parent")):
			frappe.delete_doc(sjabloon, naam, force=True, ignore_permissions=True)
	for rekening in vreemd:
		frappe.delete_doc("Account", rekening, force=True, ignore_permissions=True)


def vul_schema_aan(bedrijf: str) -> list[str]:
	"""Maakt de rekeningen van ons schema aan die dit bedrijf nog mist (een latere versie van het schema kan er een
	bij hebben). In een groep gebeurt dat bij het moederbedrijf; ERPNext zet de rekening dan ook bij de dochters."""
	gegevens = schema()
	if frappe.db.get_value("Company", bedrijf, "chart_of_accounts") != gegevens["naam"]:
		return []
	wortel = bedrijf
	while frappe.db.get_value("Company", wortel, "parent_company"):
		wortel = frappe.db.get_value("Company", wortel, "parent_company")
	nieuw = []
	for nummer, naam, ouder, soort, rgs in gegevens["rekeningen"]:
		if ouder is None or frappe.db.exists("Account", {"company": wortel, "account_number": nummer}):
			continue
		bovenliggend = frappe.db.get_value("Account", {"company": wortel, "account_number": ouder}, "name")
		if not bovenliggend:
			continue
		frappe.get_doc({"doctype": "Account", "company": wortel, "account_name": naam, "account_number": nummer, "parent_account": bovenliggend, "account_type": soort or None, "rgs_code": rgs}).insert(ignore_permissions=True)
		nieuw.append(nummer)
	if nieuw:
		for nummer, _naam, _ouder, _soort, rgs in gegevens["rekeningen"]:
			if nummer in nieuw:
				for rekening in frappe.get_all("Account", filters={"account_number": nummer, "rgs_code": ("is", "not set")}, pluck="name"):
					frappe.db.set_value("Account", rekening, "rgs_code", rgs, update_modified=False)
	return nieuw


def _werk_schema_af(bedrijf: str, gegevens: dict) -> dict:
	"""Na het zetten of overnemen van het schema: RGS-codes, standaardrekeningen, de modules en de btw-codes."""
	from openaec_bouw import profiel

	per_nummer = {
		r.account_number: r.name
		for r in frappe.get_all("Account", filters={"company": bedrijf}, fields=["name", "account_number"])
		if r.account_number
	}
	per_naam = dict(frappe.get_all("Account", filters={"company": bedrijf}, fields=["account_name", "name"], as_list=True))
	for nummer, naam, ouder, _soort, rgs in gegevens["rekeningen"]:
		rekening = per_naam.get(naam) if ouder is None else per_nummer.get(nummer)
		if rekening and rgs:
			frappe.db.set_value("Account", rekening, "rgs_code", rgs, update_modified=False)

	meta = frappe.get_meta("Company")
	standaard = {veld: per_nummer[nr] for veld, nr in gegevens["standaard"].items() if meta.has_field(veld) and nr in per_nummer}
	if meta.has_field("round_off_cost_center"):
		standaard["round_off_cost_center"] = frappe.db.get_value("Company", bedrijf, "cost_center")
	if meta.has_field("chart_of_accounts"):
		standaard["chart_of_accounts"] = gegevens["naam"]
	frappe.db.set_value("Company", bedrijf, standaard)
	_ruim_verwijzingen_op(bedrijf)

	toegepast = profiel.pas_toe() if profiel.ingeschakeld() else {}
	zet_btw_codes()
	if not frappe.flags.in_test:
		frappe.db.commit()
	return {"bedrijf": bedrijf, "schema": gegevens["naam"], "rekeningen": len(per_nummer), "modules": toegepast}


def _ruim_verwijzingen_op(bedrijf: str) -> None:
	"""Wat nog naar een rekening van het oude schema wijst, wordt leeggemaakt: velden op het bedrijf die een andere
	app erbij zette (Frappe HR), en de declaratiesoorten van Frappe HR. Anders loopt de volgende opslag daarop vast."""
	for veld in frappe.get_meta("Company").get("fields", {"fieldtype": "Link", "options": "Account"}):
		waarde = frappe.db.get_value("Company", bedrijf, veld.fieldname)
		if waarde and not frappe.db.exists("Account", waarde):
			frappe.db.set_value("Company", bedrijf, veld.fieldname, None, update_modified=False)
	if frappe.db.exists("DocType", "Expense Claim Account"):
		for rij in frappe.get_all("Expense Claim Account", filters={"company": bedrijf}, fields=["name", "default_account"]):
			if rij.default_account and not frappe.db.exists("Account", rij.default_account):
				frappe.db.delete("Expense Claim Account", {"name": rij.name})


def zet_btw_codes() -> int:
	"""Geeft de btw-sjablonen van de module Basis hun code, als die nog leeg is (op de titel van het sjabloon)."""
	from openaec_bouw import profiel

	gezet = 0
	for record in profiel.modules().get("basis", {}).get("records", []):
		codes = record.get("codes") if record.get("soort") == "btw" else None
		if not codes:
			continue
		for doctype, sleutel in (("Sales Taxes and Charges Template", "verkoop"), ("Purchase Taxes and Charges Template", "inkoop")):
			for naam in frappe.get_all(doctype, filters={"title": record["naam"], "btw_code": ("is", "not set")}, pluck="name"):
				frappe.db.set_value(doctype, naam, "btw_code", codes[sleutel], update_modified=False)
				gezet += 1
	return gezet


def zorg_voor_velden() -> None:
	if "erpnext" in frappe.get_installed_apps():
		create_custom_fields(_velden(), ignore_validate=True)


def na_migratie() -> None:
	"""Vóór het profiel: de velden, daarna een RGS-voorstel waar het leeg is en de btw-codes van onze sjablonen."""
	try:
		zorg_voor_velden()
		if frappe.db.has_column("Account", "rgs_code"):
			vul_rgs_aan()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="OpenAEC Bouw: boekhouding voorbereiden mislukt")


def na_profiel() -> None:
	"""Na het profiel: de btw-codes op de sjablonen die de module Basis zette."""
	try:
		if frappe.db.has_column("Sales Taxes and Charges Template", "btw_code"):
			zet_btw_codes()
			frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="OpenAEC Bouw: btw-codes zetten mislukt")
