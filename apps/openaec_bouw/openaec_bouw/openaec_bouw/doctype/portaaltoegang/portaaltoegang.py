import frappe
from frappe import _
from frappe.model.document import Document


class Portaaltoegang(Document):
	def validate(self):
		self.email = (self.email or "").strip().lower()
		dubbel = frappe.db.exists(
			"Portaaltoegang", {"project": self.project, "email": self.email, "name": ["!=", self.name]}
		)
		if dubbel:
			frappe.throw(_("{0} heeft al toegang tot dit project.").format(self.email))
