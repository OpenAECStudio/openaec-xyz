"""Opgaaf ICP: de leveringen en diensten aan afnemers in andere EU-landen, per btw-nummer.

Telt de geboekte verkoopfacturen met een btw-sjabloon met code VEU (rubriek 3b van de aangifte). Een hulpmiddel bij de
opgaaf, geen opgaaf: controleer de cijfers en de btw-nummers voor het indienen.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not (filters.company and filters.van and filters.tot):
		frappe.throw(_("Kies een bedrijf en een tijdvak"))
	if getdate(filters.van) > getdate(filters.tot):
		frappe.throw(_("Het begin van het tijdvak ligt na het einde"))
	rijen = bereken(filters.company, filters.van, filters.tot)
	zonder = [r["klant"] for r in rijen if not r["btw_nummer"]]
	melding = _("Zonder btw-nummer: {0}").format(", ".join(zonder)) if zonder else None
	return kolommen(), rijen, melding


def kolommen() -> list[dict]:
	return [
		{"fieldname": "klant", "label": _("Klant"), "fieldtype": "Link", "options": "Customer", "width": 280},
		{"fieldname": "btw_nummer", "label": _("Btw-nummer"), "fieldtype": "Data", "width": 180},
		{"fieldname": "facturen", "label": _("Facturen"), "fieldtype": "Int", "width": 100},
		{"fieldname": "bedrag", "label": _("Bedrag"), "fieldtype": "Currency", "width": 160},
	]


def bereken(bedrijf: str, van, tot) -> list[dict]:
	sjabloon = "Sales Taxes and Charges Template"
	if not frappe.db.has_column(sjabloon, "btw_code"):
		return []
	sjablonen = frappe.get_all(sjabloon, filters={"company": bedrijf, "btw_code": "VEU"}, pluck="name")
	if not sjablonen:
		return []
	facturen = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 1, "company": bedrijf, "posting_date": ("between", [van, tot]), "taxes_and_charges": ("in", sjablonen)},
		fields=["customer", "tax_id", "base_net_total"],
	)
	per_klant = {}
	for f in facturen:
		rij = per_klant.setdefault(f.customer, {"klant": f.customer, "btw_nummer": None, "facturen": 0, "bedrag": 0.0})
		rij["btw_nummer"] = rij["btw_nummer"] or f.tax_id or frappe.db.get_value("Customer", f.customer, "tax_id")
		rij["facturen"] += 1
		rij["bedrag"] = flt(rij["bedrag"] + flt(f.base_net_total), 2)
	return sorted(per_klant.values(), key=lambda r: r["klant"])
