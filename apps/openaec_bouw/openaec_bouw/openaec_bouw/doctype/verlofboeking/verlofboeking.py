"""Eén boeking in het verlofsaldo, in uren. Opbouw, opname en verval boekt het systeem; met de hand alleen een
startsaldo, een correctie of een uitbetaling, altijd met een reden."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class Verlofboeking(Document):
	def validate(self):
		if not self.flags.door_systeem and self.soort not in ("Startsaldo", "Correctie", "Uitbetaling"):
			frappe.throw(_("Opbouw, opname en verval boekt het systeem. Met de hand kan alleen een startsaldo, een correctie of een uitbetaling."))
		if self.soort == "Startsaldo" and flt(self.uren) < 0:
			frappe.throw(_("Een startsaldo is nul of meer; een tekort is een correctie."))
		if self.soort in ("Opname", "Verval", "Uitbetaling") and flt(self.uren) > 0:
			self.uren = -flt(self.uren)
		if not self.opbouwjaar and self.soort in ("Startsaldo", "Opbouw", "Correctie"):
			self.opbouwjaar = getdate(self.datum).year
