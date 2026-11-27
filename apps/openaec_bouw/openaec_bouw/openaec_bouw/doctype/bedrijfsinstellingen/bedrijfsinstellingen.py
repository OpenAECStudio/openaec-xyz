"""Instellingen van één bedrijf; zie `openaec_bouw.bedrijfsinstellingen`."""

import frappe
from frappe import _
from frappe.model.document import Document


class Bedrijfsinstellingen(Document):
	def validate(self):
		dagen = [(r.week or "", r.weekdag) for r in self.werkweek]
		if len(dagen) != len(set(dagen)):
			frappe.throw(_("Een weekdag staat twee keer in de werkweek."))
		soorten = [r.kostensoort for r in self.toeslagen]
		if len(soorten) != len(set(soorten)):
			frappe.throw(_("Een kostensoort staat twee keer bij de toeslagen."))
