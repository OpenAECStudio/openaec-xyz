"""Vrije dagen van één bedrijf in één jaar voor één cao-groep; vastgesteld wordt het de feestdagenlijst van Frappe."""

import frappe
from frappe import _
from frappe.model.document import Document

from openaec_bouw import personeel


class Bedrijfskalender(Document):
	def validate(self):
		datums = [str(r.datum) for r in self.dagen]
		if len(datums) != len(set(datums)):
			frappe.throw(_("Een datum staat twee keer in de kalender."))
		for r in self.dagen:
			if str(r.datum)[:4] != str(self.jaar):
				frappe.throw(_("{0} valt niet in {1}.").format(r.datum, self.jaar))
		self.dagen.sort(key=lambda r: str(r.datum))
		for i, r in enumerate(self.dagen, 1):
			r.idx = i


@frappe.whitelist()
def vernieuwen(naam: str):
	doc = frappe.get_doc("Bedrijfskalender", naam)
	doc.check_permission("write")
	return personeel.maak_kalender(doc.bedrijf, doc.jaar, doc.cao, doc.werknemersgroep).name


@frappe.whitelist()
def vaststellen(naam: str):
	frappe.get_doc("Bedrijfskalender", naam).check_permission("write")
	return personeel.kalender_vaststellen(naam).name
