"""Btw-aangifte: de aangifte omzetbelasting van één bedrijf over één tijdvak, als document.

Het rapport Btw-aangifte rekent de rubrieken uit; dit document legt ze vast, zodat te zien blijft wat er is aangegeven
en wanneer. Als concept ververst het bij elke opslag. Indienen (submit) zet de cijfers vast, en kan pas als er in het
tijdvak geen conceptfacturen meer staan. De journaalpost boekt de btw-rekeningen leeg naar Btw-afdracht.

Het indienen bij de Belastingdienst zelf gebeurt hier niet: de cijfers neem je over in Mijn Belastingdienst Zakelijk.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, formatdate, getdate

from openaec_bouw.openaec_bouw.report.btw_aangifte.btw_aangifte import bereken, rijen

AFDRACHT = "1590"  # Btw-afdracht in het rekeningschema van OpenAEC Bouw


class Btwaangifte(Document):
	def validate(self):
		if getdate(self.van) > getdate(self.tot):
			frappe.throw(_("Het begin van het tijdvak ligt na het einde."))
		overlap = frappe.get_all(
			"Btw-aangifte",
			filters={"bedrijf": self.bedrijf, "docstatus": ("<", 2), "name": ("!=", self.name or ""), "van": ("<=", self.tot), "tot": (">=", self.van)},
			pluck="name",
			limit=1,
		)
		if overlap:
			frappe.throw(_("Er is al een aangifte voor {0} die dit tijdvak raakt: {1}.").format(self.bedrijf, overlap[0]))
		self.titel = f"{self.bedrijf} {formatdate(self.van, 'dd-MM-yyyy')} t/m {formatdate(self.tot, 'dd-MM-yyyy')}"
		if self.docstatus == 0:
			self.vul_cijfers()

	def vul_cijfers(self) -> None:
		cijfers = bereken(self.bedrijf, self.van, self.tot, concepten=bool(self.concepten_meetellen))
		self.set("regels", [{"rubriek": r["rubriek"], "omschrijving": r["omschrijving"], "omzet": r["omzet"], "btw": r["btw"]} for r in rijen(cijfers)])
		self.verschuldigd = cijfers["5a"]["btw"]
		self.voorbelasting = cijfers["5b"]["btw"]
		self.te_betalen = cijfers["5c"]["btw"]

	def before_submit(self):
		for doctype in ("Sales Invoice", "Purchase Invoice"):
			concepten = frappe.db.count(doctype, {"company": self.bedrijf, "docstatus": 0, "posting_date": ("between", [self.van, self.tot])})
			if concepten:
				frappe.throw(_("In dit tijdvak staan nog {0} concepten ({1}). Boek of verwijder ze voor het indienen.").format(concepten, _(doctype)))
		self.concepten_meetellen = 0
		self.vul_cijfers()
		if not self.ingediend_op:
			self.ingediend_op = frappe.utils.today()

	def on_cancel(self):
		if self.journaalpost and frappe.db.get_value("Journal Entry", self.journaalpost, "docstatus") == 1:
			frappe.throw(_("Annuleer eerst journaalpost {0}.").format(self.journaalpost))

	def saldi(self) -> dict:
		"""Per btw-rekening wat er in het tijdvak op de facturen staat: positief = af te dragen, negatief = te vorderen."""
		status = "f.docstatus < 2" if self.concepten_meetellen and self.docstatus == 0 else "f.docstatus = 1"
		uit = {}
		for doctype, kind, teken in (("Sales Invoice", "Sales Taxes and Charges", 1), ("Purchase Invoice", "Purchase Taxes and Charges", -1)):
			bedrag = "t.base_tax_amount_after_discount_amount"
			if teken < 0:
				bedrag = f"case when ifnull(t.add_deduct_tax, 'Add') = 'Deduct' then -{bedrag} else {bedrag} end"
			for rij in frappe.db.sql(
				f"""select t.account_head, sum({bedrag}) as bedrag from `tab{kind}` t join `tab{doctype}` f on f.name = t.parent
				where f.company = %s and {status} and f.posting_date between %s and %s group by t.account_head""",
				(self.bedrijf, self.van, self.tot),
				as_dict=True,
			):
				uit[rij.account_head] = flt(uit.get(rij.account_head, 0) + teken * flt(rij.bedrag), 2)
		return {rekening: bedrag for rekening, bedrag in uit.items() if bedrag}

	@frappe.whitelist()
	def maak_journaalpost(self) -> str | None:
		"""Een concept-journaalpost die de btw-rekeningen van het tijdvak leegboekt naar Btw-afdracht."""
		self.check_permission("write")
		if self.journaalpost and frappe.db.get_value("Journal Entry", self.journaalpost, "docstatus") != 2:
			frappe.throw(_("Er is al een journaalpost: {0}.").format(self.journaalpost))
		afdracht = frappe.db.get_value("Account", {"company": self.bedrijf, "account_number": AFDRACHT}, "name")
		if not afdracht:
			frappe.throw(_("Het bedrijf heeft geen rekening {0} (Btw-afdracht).").format(AFDRACHT))
		regels, totaal = [], 0.0
		for rekening, bedrag in sorted(self.saldi().items()):
			regels.append({"account": rekening, "debit_in_account_currency": bedrag if bedrag > 0 else 0, "credit_in_account_currency": -bedrag if bedrag < 0 else 0})
			totaal = flt(totaal + bedrag, 2)
		if not regels or not totaal:
			return None
		regels.append({"account": afdracht, "debit_in_account_currency": -totaal if totaal < 0 else 0, "credit_in_account_currency": totaal if totaal > 0 else 0})
		post = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"company": self.bedrijf,
				"posting_date": self.tot,
				"voucher_type": "Journal Entry",
				"user_remark": _("Btw-aangifte {0}").format(self.titel),
				"accounts": regels,
			}
		).insert()
		self.db_set("journaalpost", post.name)
		return post.name
