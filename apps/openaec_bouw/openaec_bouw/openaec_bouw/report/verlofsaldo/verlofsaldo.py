"""Verlofsaldo per medewerker en verlofsoort over een periode, in uren: begin, opbouw, opname, verval, eind, en wat
er als eerste vervalt."""

import frappe
from frappe import _
from frappe.utils import flt, getdate

from openaec_bouw import personeel


def execute(filters=None):
	filters = frappe._dict(filters or {})
	van, tot = getdate(filters.van), getdate(filters.tot)
	voorwaarden = {"datum": ("<=", tot)}
	if filters.company:
		voorwaarden["bedrijf"] = filters.company
	if filters.medewerker:
		voorwaarden["medewerker"] = filters.medewerker
	if filters.verlofsoort:
		voorwaarden["verlofsoort"] = filters.verlofsoort
	boekingen = frappe.get_all("Verlofboeking", filters=voorwaarden, fields=["medewerker", "medewerker_naam", "verlofsoort", "soort", "datum", "uren"])

	rijen = {}
	for b in boekingen:
		rij = rijen.setdefault((b.medewerker, b.verlofsoort), frappe._dict(
			medewerker=b.medewerker, naam=b.medewerker_naam, verlofsoort=b.verlofsoort,
			begin=0.0, opbouw=0.0, opname=0.0, verval=0.0, overig=0.0,
		))
		if getdate(b.datum) < van:
			rij.begin += b.uren
		elif b.soort in ("Opbouw", "Startsaldo"):
			rij.opbouw += b.uren
		elif b.soort == "Opname":
			rij.opname += b.uren
		elif b.soort == "Verval":
			rij.verval += b.uren
		else:
			rij.overig += b.uren

	data = []
	for (medewerker, soort), rij in sorted(rijen.items(), key=lambda x: (x[1].naam or "", x[0][1])):
		rij.eind = rij.begin + rij.opbouw + rij.opname + rij.verval + rij.overig
		contract = personeel.contract_op(medewerker, tot)
		per_dag = (flt(contract.uren_per_week) / 5) if contract and contract.uren_per_week else 8
		rij.eind_dagen = rij.eind / per_dag if per_dag else 0
		rij.vervalt_op, rij.vervalt_uren = _eerst_vervallend(medewerker, soort, tot)
		for k in ("begin", "opbouw", "opname", "verval", "overig", "eind", "eind_dagen", "vervalt_uren"):
			rij[k] = flt(rij[k], 2)
		data.append(rij)
	return _kolommen(), data


def _eerst_vervallend(medewerker, soort, datum):
	stand = personeel.per_opbouwjaar(medewerker, soort, datum)
	for jaar in sorted(stand["jaren"]):
		rest = stand["jaren"][jaar]
		if rest <= 0:
			continue
		grens = personeel.vervaldatum(personeel._verval_regel(soort, stand["regels"].get(jaar)), jaar)
		if grens:
			return grens, rest
	return None, 0


def _kolommen():
	uren = {"fieldtype": "Float", "width": 100, "precision": 2}
	return [
		{"fieldname": "medewerker", "label": _("Medewerker"), "fieldtype": "Link", "options": "Employee", "width": 120},
		{"fieldname": "naam", "label": _("Naam"), "fieldtype": "Data", "width": 180},
		{"fieldname": "verlofsoort", "label": _("Verlofsoort"), "fieldtype": "Link", "options": "Leave Type", "width": 180},
		{"fieldname": "begin", "label": _("Begin"), **uren},
		{"fieldname": "opbouw", "label": _("Opbouw"), **uren},
		{"fieldname": "opname", "label": _("Opname"), **uren},
		{"fieldname": "verval", "label": _("Verval"), **uren},
		{"fieldname": "overig", "label": _("Correctie en uitbetaling"), **uren},
		{"fieldname": "eind", "label": _("Eind (uren)"), **uren},
		{"fieldname": "eind_dagen", "label": _("Eind (dagen)"), **uren},
		{"fieldname": "vervalt_uren", "label": _("Vervalt eerst (uren)"), **uren},
		{"fieldname": "vervalt_op", "label": _("Op"), "fieldtype": "Date", "width": 100},
	]
