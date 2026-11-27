"""Eén looptijd van een cao voor één werknemersgroep. Wat er op een datum geldt: `personeel.periode_op`."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class CaoPeriode(Document):
	def autoname(self):
		self.name = f"{self.cao} {self.werknemersgroep} {getdate(self.geldig_van).isoformat()}"

	def validate(self):
		groepen = [r.groep for r in frappe.get_doc("Cao", self.cao).werknemersgroepen]
		if groepen and self.werknemersgroep not in groepen:
			frappe.throw(_("Werknemersgroep {0} hoort niet bij cao {1}. Kies uit: {2}.").format(self.werknemersgroep, self.cao, ", ".join(groepen)))
		if self.geldig_tot and getdate(self.geldig_tot) < getdate(self.geldig_van):
			frappe.throw(_("Geldig tot ligt voor geldig van."))
		eind = self.geldig_tot or "9999-12-31"
		for ander in frappe.get_all("Cao Periode", filters={"cao": self.cao, "werknemersgroep": self.werknemersgroep, "name": ("!=", self.name or "")}, fields=["name", "geldig_van", "geldig_tot"]):
			if getdate(ander.geldig_van) <= getdate(eind) and getdate(ander.geldig_tot or "9999-12-31") >= getdate(self.geldig_van):
				frappe.throw(_("Deze periode overlapt met {0}.").format(ander.name))
		soorten = [r.verlofsoort for r in self.verlofrechten]
		if len(soorten) != len(set(soorten)):
			frappe.throw(_("Een verlofsoort staat twee keer bij de verlofrechten."))
		if self.status != "Concept" and self.has_value_changed("status") and not self.nagelopen_door:
			self.nagelopen_door, self.nagelopen_op = frappe.session.user, getdate()

	def on_trash(self):
		if frappe.db.exists("Verlofboeking", {"cao_periode": self.name}):
			frappe.throw(_("Er zijn verlofboekingen op deze periode gemaakt; corrigeer met een nieuwe periode."))
