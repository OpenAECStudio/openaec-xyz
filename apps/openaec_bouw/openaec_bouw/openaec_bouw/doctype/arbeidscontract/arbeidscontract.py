"""Arbeidscontract: soort, looptijd, uren, werkpatroon en cao van één medewerker. Een verlenging is een nieuw contract."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, add_years, date_diff, flt, getdate, today

from openaec_bouw import bedrijfsinstellingen, personeel


class Arbeidscontract(Document):
	@property
	def cao_periode_nu(self):
		return personeel.periode_op(self.cao, self.werknemersgroep, today()) if self.cao else None

	@property
	def cao_periode_volgende(self):
		return personeel.volgende_periode(self.cao, self.werknemersgroep, today()) if self.cao else None

	def validate(self):
		if self.tot and getdate(self.tot) < getdate(self.van):
			frappe.throw(_("Het contract eindigt voor het begint."))
		self._geen_overlap()
		if self.cao:
			groepen = [r.groep for r in frappe.get_cached_doc("Cao", self.cao).werknemersgroepen]
			if not self.werknemersgroep and len(groepen) == 1:
				self.werknemersgroep = groepen[0]
			if self.werknemersgroep not in groepen:
				frappe.throw(_("Kies een werknemersgroep van cao {0}: {1}.").format(self.cao, ", ".join(groepen)))
		if not self.werkpatroon and self.soort not in personeel.ZONDER_ROOSTER:
			self._werkpatroon_voorstellen()
		if self.soort == "Min-maxcontract" and flt(self.max_uren) < flt(self.min_uren):
			frappe.throw(_("Het maximum aantal uren is lager dan het minimum."))
		self._uren_kloppen()
		periode = personeel.periode_op(self.cao, self.werknemersgroep, max(getdate(self.van), getdate(today()))) if self.cao else None
		self.contractfactor = personeel.contractfactor(self, periode)
		vandaag = getdate(today())
		self.status = "Toekomstig" if getdate(self.van) > vandaag else "Afgelopen" if self.tot and getdate(self.tot) < vandaag else "Lopend"
		self._keten()

	def on_update(self):
		personeel.medewerker_bijwerken(self.medewerker)
		personeel.kalenders_toewijzen(self)

	def _geen_overlap(self):
		eind = self.tot or "9999-12-31"
		for ander in frappe.get_all("Arbeidscontract", filters={"medewerker": self.medewerker, "name": ("!=", self.name or "")}, fields=["name", "van", "tot"]):
			if getdate(ander.van) <= getdate(eind) and getdate(ander.tot or "9999-12-31") >= getdate(self.van):
				frappe.throw(_("Dit contract overlapt met {0}. Laat het vorige contract eerst eindigen.").format(ander.name))

	def _werkpatroon_voorstellen(self):
		"""De werkweek van het bedrijf, naar rato van de uren per week."""
		week = bedrijfsinstellingen.werkweek(self.bedrijf) if self.bedrijf else dict(bedrijfsinstellingen.STANDAARD_WERKWEEK)
		totaal = sum(week.values()) or 40
		factor = flt(self.uren_per_week) / totaal if self.uren_per_week else 1
		for dag in bedrijfsinstellingen.WEEKDAGEN:
			self.append("werkpatroon", {"weekdag": dag, "uren": flt(week.get(dag, 0) * factor, 2)})
		if not self.uren_per_week:
			self.uren_per_week = totaal

	def _uren_kloppen(self):
		if self.soort in personeel.ZONDER_ROOSTER or not self.uren_per_week:
			return
		a = sum(flt(r.uren) for r in self.werkpatroon if (r.week or "") in ("", "A"))
		b = sum(flt(r.uren) for r in self.werkpatroon if (r.week or "") in ("", "B"))
		gemiddeld = (a + b) / 2 if any(r.week for r in self.werkpatroon) else a
		if abs(gemiddeld - flt(self.uren_per_week)) > 0.01:
			frappe.msgprint(
				_("Het werkpatroon telt gemiddeld {0} uur per week, het contract {1}.").format(flt(gemiddeld, 2), flt(self.uren_per_week, 2)),
				indicator="orange", alert=True,
			)

	def _keten(self):
		"""Ketenregeling: meer dan drie contracten voor bepaalde tijd, of langer dan drie jaar, met tussenpozen van
		zes maanden of korter. Een cao kan afwijken; daarom een waarschuwing en geen blokkade."""
		if self.soort not in ("Bepaalde tijd", "Min-maxcontract", "Nulurencontract", "Oproepcontract"):
			return
		vorige = frappe.get_all(
			"Arbeidscontract",
			filters={"medewerker": self.medewerker, "name": ("!=", self.name or ""), "van": ("<", self.van), "soort": ("!=", "Onbepaalde tijd")},
			fields=["van", "tot"], order_by="van desc",
		)
		keten, eind_vorige = [self], getdate(self.van)
		for c in vorige:
			if not c.tot or date_diff(eind_vorige, c.tot) > 183:
				break
			keten.append(c)
			eind_vorige = getdate(c.van)
		begin = getdate(keten[-1].van)
		einde = getdate(self.tot) if self.tot else None
		if len(keten) > 3 or (einde and einde > add_years(begin, 3)):
			frappe.msgprint(
				_("Ketenregeling: dit is contract {0} in een keten die begon op {1}. Volgens de wet wordt dit een contract voor onbepaalde tijd, tenzij de cao anders bepaalt.").format(len(keten), frappe.format(begin, "Date")),
				title=_("Let op"), indicator="orange",
			)
		if einde and date_diff(einde, self.van) >= 182 and getdate(today()) >= getdate(add_months(einde, -2)):
			frappe.msgprint(_("Aanzegplicht: uiterlijk een maand voor {0} laten weten of het contract wordt verlengd.").format(frappe.format(einde, "Date")), indicator="orange", alert=True)
