"""Btw-aangifte: de rubrieken van de Nederlandse aangifte omzetbelasting over een tijdvak.

Leest de geboekte verkoop- en inkoopfacturen van het bedrijf. De rubriek volgt uit de btw-code van het btw-sjabloon
op de factuur (`openaec_bouw.boekhouding.BTW_CODES`); een factuur met een sjabloon zonder code valt terug op het tarief
van de btw-regels en op het woord "verlegd". Rubrieken: 1a, 1b, 1c, 1e, 2a, 3a, 3b, 4a, 4b en 5a tot en met 5c.
Niet: 1d (privégebruik), 3c (afstandsverkopen) en suppletie. Een hulpmiddel bij de aangifte, geen aangifte:
controleer de cijfers voor het indienen.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate

from openaec_bouw.boekhouding import BTW_CODES

HOOG, LAAG = 21.0, 9.0
VERLEGD = "verlegd"
# Onder dit verschil is een rest afronding van de btw per regel, geen omzet tegen 0%.
AFRONDING = 0.50


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not (filters.company and filters.van and filters.tot):
		frappe.throw(_("Kies een bedrijf en een tijdvak"))
	if getdate(filters.van) > getdate(filters.tot):
		frappe.throw(_("Het begin van het tijdvak ligt na het einde"))
	cijfers = bereken(filters.company, filters.van, filters.tot)
	melding = _("Rubriek 1d, 3c en suppleties zitten niet in dit overzicht. Controleer de cijfers voor het indienen.")
	return kolommen(), rijen(cijfers), melding


def kolommen() -> list[dict]:
	return [
		{"fieldname": "rubriek", "label": _("Rubriek"), "fieldtype": "Data", "width": 90},
		{"fieldname": "omschrijving", "label": _("Omschrijving"), "fieldtype": "Data", "width": 460},
		{"fieldname": "omzet", "label": _("Omzet"), "fieldtype": "Currency", "width": 160},
		{"fieldname": "btw", "label": _("Btw"), "fieldtype": "Currency", "width": 160},
	]


def _facturen(doctype: str, bedrijf: str, van, tot, concepten: bool = False) -> list[frappe._dict]:
	"""De geboekte facturen in het tijdvak (met `concepten` ook de concepten), elk met zijn btw-regels (`regels`)."""
	facturen = frappe.get_all(
		doctype,
		filters={"docstatus": ("in", [0, 1]) if concepten else 1, "company": bedrijf, "posting_date": ("between", [van, tot])},
		fields=["name", "base_net_total", "taxes_and_charges"],
	)
	if not facturen:
		return []
	velden = ["parent", "rate", "account_head", "description", "base_tax_amount_after_discount_amount as bedrag"]
	if doctype == "Purchase Invoice":
		velden += ["category", "add_deduct_tax"]
	regels = frappe.get_all(
		f"{doctype.split()[0]} Taxes and Charges",
		filters={"parenttype": doctype, "parent": ("in", [f.name for f in facturen])},
		fields=velden,
	)
	per_factuur = {}
	for regel in regels:
		per_factuur.setdefault(regel.parent, []).append(regel)
	sjablonen = {f.taxes_and_charges for f in facturen if f.taxes_and_charges}
	sjabloon = f"{doctype.split()[0]} Taxes and Charges Template"
	codes = {}
	if sjablonen and frappe.db.has_column(sjabloon, "btw_code"):
		codes = dict(frappe.get_all(sjabloon, filters={"name": ("in", list(sjablonen))}, fields=["name", "btw_code"], as_list=True))
	for factuur in facturen:
		factuur.regels = per_factuur.get(factuur.name, [])
		factuur.code = codes.get(factuur.taxes_and_charges) or None
	return facturen


def _is_verlegd(factuur: frappe._dict) -> bool:
	teksten = [factuur.taxes_and_charges, *[r.account_head for r in factuur.regels], *[r.description for r in factuur.regels]]
	return any(VERLEGD in (t or "").lower() for t in teksten)


def bereken(bedrijf: str, van, tot, concepten: bool = False) -> dict:
	"""De rubrieken als `{rubriek: {"omzet": ..., "btw": ...}}`, in de valuta van het bedrijf. Met `concepten` tellen ook
	conceptfacturen mee (voor een voorlopige stand)."""
	uit = {r: {"omzet": 0.0, "btw": 0.0} for r in ("1a", "1b", "1c", "1e", "2a", "3a", "3b", "4a", "4b", "5b")}
	btw_rekeningen = set(frappe.get_all("Account", filters={"company": bedrijf, "account_type": "Tax"}, pluck="name"))

	for factuur in _facturen("Sales Invoice", bedrijf, van, tot, concepten):
		if factuur.code in ("V0", "VVERL", "VEXP", "VEU"):
			# Geen Nederlandse btw op de factuur: de hele omzet in de rubriek van de code.
			uit[BTW_CODES[factuur.code]]["omzet"] += flt(factuur.base_net_total)
			continue
		belast = 0.0
		grootste = None
		for regel in factuur.regels:
			tarief = flt(regel.rate)
			if tarief <= 0:
				continue
			rubriek = "1a" if tarief == HOOG else "1b" if tarief == LAAG else "1c"
			grondslag = flt(regel.bedrag) / tarief * 100
			uit[rubriek]["omzet"] += grondslag
			uit[rubriek]["btw"] += flt(regel.bedrag)
			belast += grondslag
			if grootste is None or abs(grondslag) > abs(grootste[1]):
				grootste = (rubriek, grondslag)
		rest = flt(factuur.base_net_total) - belast
		if grootste and abs(rest) < AFRONDING:
			uit[grootste[0]]["omzet"] += rest
		else:
			uit["1e"]["omzet"] += rest

	for factuur in _facturen("Purchase Invoice", bedrijf, van, tot, concepten):
		for regel in factuur.regels:
			if regel.account_head not in btw_rekeningen or regel.category == "Valuation":
				continue
			teken = -1 if regel.add_deduct_tax == "Deduct" else 1
			uit["5b"]["btw"] += teken * flt(regel.bedrag)
		rubriek = BTW_CODES.get(factuur.code) if factuur.code in ("IVERL", "IBUI", "IEU") else None
		if not rubriek and not factuur.code and _is_verlegd(factuur):
			rubriek = "2a"
		if rubriek:
			# De btw is naar ons verlegd (binnenland 2a, buiten de EU 4a, binnen de EU 4b): aangeven en als
			# voorbelasting aftrekken (5b).
			btw = flt(factuur.base_net_total) * HOOG / 100
			uit[rubriek]["omzet"] += flt(factuur.base_net_total)
			uit[rubriek]["btw"] += btw
			uit["5b"]["btw"] += btw

	for rubriek in uit.values():
		rubriek["omzet"], rubriek["btw"] = flt(rubriek["omzet"], 2), flt(rubriek["btw"], 2)
	uit["5a"] = {"omzet": None, "btw": flt(sum(uit[r]["btw"] for r in ("1a", "1b", "1c", "2a", "4a", "4b")), 2)}
	uit["5c"] = {"omzet": None, "btw": flt(uit["5a"]["btw"] - uit["5b"]["btw"], 2)}
	return uit


def rijen(cijfers: dict) -> list[dict]:
	teksten = [
		("1a", _("Leveringen en diensten belast met het hoge tarief (21%)")),
		("1b", _("Leveringen en diensten belast met het lage tarief (9%)")),
		("1c", _("Leveringen en diensten belast met overige tarieven")),
		("1e", _("Leveringen en diensten belast met 0% of niet bij u belast (ook verlegd)")),
		("2a", _("Leveringen en diensten waarbij de btw naar u is verlegd")),
		("3a", _("Leveringen naar landen buiten de EU (uitvoer)")),
		("3b", _("Leveringen naar of diensten in landen binnen de EU")),
		("4a", _("Leveringen en diensten uit landen buiten de EU")),
		("4b", _("Leveringen en diensten uit landen binnen de EU")),
		("5a", _("Verschuldigde btw (rubriek 1, 2 en 4)")),
		("5b", _("Voorbelasting")),
		("5c", _("Te betalen (of bij een negatief bedrag: terug te vragen)")),
	]
	uit = []
	for rubriek, tekst in teksten:
		rij = {"rubriek": rubriek, "omschrijving": tekst, **cijfers[rubriek], "vet": rubriek in ("5a", "5c")}
		if rubriek in ("1e", "3a", "3b", "5b"):
			rij["omzet" if rubriek == "5b" else "btw"] = None
		uit.append(rij)
	return uit
