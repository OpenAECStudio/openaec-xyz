"""Onderhanden werk: de stand van de lopende projecten van één bedrijf op een peildatum.

Een aannemer factureert in termijnen en maakt kosten in een ander tempo. Op een peildatum staat een project daardoor
voor (meer gefactureerd dan gemaakt) of achter. Dit document rekent per lopend project uit:

- kosten tot de peildatum (inkoopfacturen op het project) en gefactureerde termijnen (verkoopfacturen);
- de voortgang: kosten gedeeld door de begrote kosten;
- het verwachte resultaat: aanneemsom min de begrote kosten (of de werkelijke, als die hoger zijn);
- het genomen resultaat: naar voortgang, of pas bij oplevering; een verwacht verlies altijd meteen en volledig;
- het saldo: kosten plus genomen resultaat min gefactureerd.

De journaalpost zet het verschil met de vorige stand op de balans: een positief saldo op Onderhanden projecten (3100),
een negatief op Gefactureerde termijnen (3110), met Mutatie onderhanden projecten (8090) als tegenrekening. Zo volgt
het resultaat van een periode het werk en niet het moment van factureren.

Uren van eigen mensen tellen nog niet mee als kosten; dat komt met de urenstaten. Welke methode past, is een keuze
van het bedrijf met zijn accountant.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, formatdate

ACTIEF, PASSIEF, MUTATIE = "3100", "3110", "8090"


class OnderhandenWerk(Document):
	def validate(self):
		dubbel = frappe.db.exists("Onderhanden Werk", {"bedrijf": self.bedrijf, "peildatum": self.peildatum, "docstatus": ("<", 2), "name": ("!=", self.name or "")})
		if dubbel:
			frappe.throw(_("Er is al een stand van {0} op {1}: {2}.").format(self.bedrijf, formatdate(self.peildatum), dubbel))
		self.titel = f"{self.bedrijf} {formatdate(self.peildatum, 'dd-MM-yyyy')}"
		if self.docstatus == 0:
			self.vul_regels()

	def _status(self) -> tuple:
		return (0, 1) if self.concepten_meetellen and self.docstatus == 0 else (1,)

	def _som(self, doctype: str, projecten: list[str]) -> dict:
		"""Per project het bedrag zonder btw op de regels van deze facturen tot en met de peildatum."""
		if not projecten:
			return {}
		rijen = frappe.db.sql(
			f"""select r.project, sum(r.base_net_amount) as bedrag from `tab{doctype} Item` r join `tab{doctype}` f on f.name = r.parent
			where f.company = %(bedrijf)s and f.docstatus in %(status)s and f.posting_date <= %(peildatum)s and r.project in %(projecten)s
			group by r.project""",
			{"bedrijf": self.bedrijf, "status": self._status(), "peildatum": self.peildatum, "projecten": projecten},
			as_dict=True,
		)
		return {r.project: flt(r.bedrag, 2) for r in rijen}

	def vul_regels(self) -> None:
		velden = ["name", "project_name", "estimated_costing"]
		if frappe.db.has_column("Project", "aanneemsom"):
			velden.append("aanneemsom")
		# Lopend op de peildatum: begonnen, niet geannuleerd, en niet vóór de peildatum opgeleverd.
		projecten = [
			p
			for p in frappe.get_all("Project", filters={"company": self.bedrijf, "status": ("!=", "Cancelled"), "expected_start_date": ("<=", self.peildatum)}, fields=[*velden, "status", "expected_end_date"], order_by="name")
			if not (p.status == "Completed" and p.expected_end_date and str(p.expected_end_date) <= str(self.peildatum))
		]
		namen = [p.name for p in projecten]
		kosten, gefactureerd = self._som("Purchase Invoice", namen), self._som("Sales Invoice", namen)
		regels = []
		for p in projecten:
			gemaakt, termijnen = kosten.get(p.name, 0), gefactureerd.get(p.name, 0)
			if not gemaakt and not termijnen:
				continue
			aanneemsom, begroot = flt(p.get("aanneemsom")), flt(p.estimated_costing)
			voortgang = min(100.0, gemaakt / begroot * 100) if begroot else 0.0
			verwacht = aanneemsom - max(begroot, gemaakt) if aanneemsom else 0.0
			if verwacht < 0:
				genomen = verwacht
			elif self.methode == "Naar voortgang":
				genomen = verwacht * voortgang / 100
			else:
				genomen = 0.0
			regels.append(
				{
					"project": p.name,
					"projectnaam": p.project_name,
					"aanneemsom": aanneemsom,
					"begrote_kosten": begroot,
					"kosten": gemaakt,
					"gefactureerd": termijnen,
					"voortgang": flt(voortgang, 1),
					"verwacht_resultaat": flt(verwacht, 2),
					"genomen_resultaat": flt(genomen, 2),
					"saldo": flt(gemaakt + genomen - termijnen, 2),
				}
			)
		self.set("regels", regels)
		self.kosten = flt(sum(r["kosten"] for r in regels), 2)
		self.gefactureerd = flt(sum(r["gefactureerd"] for r in regels), 2)
		self.genomen_resultaat = flt(sum(r["genomen_resultaat"] for r in regels), 2)
		self.te_factureren = flt(sum(r["saldo"] for r in regels if r["saldo"] > 0), 2)
		self.vooruitgefactureerd = flt(-sum(r["saldo"] for r in regels if r["saldo"] < 0), 2)

	def before_submit(self):
		projecten = [r.project for r in self.regels]
		for doctype in ("Sales Invoice", "Purchase Invoice"):
			if projecten and frappe.db.sql(
				f"""select 1 from `tab{doctype} Item` r join `tab{doctype}` f on f.name = r.parent
				where f.company = %s and f.docstatus = 0 and f.posting_date <= %s and r.project in %s limit 1""",
				(self.bedrijf, self.peildatum, projecten),
			):
				frappe.throw(_("Op deze projecten staan tot de peildatum nog concepten ({0}). Boek of verwijder ze eerst.").format(_(doctype)))
		self.concepten_meetellen = 0
		self.vul_regels()

	def on_cancel(self):
		if self.journaalpost and frappe.db.get_value("Journal Entry", self.journaalpost, "docstatus") == 1:
			frappe.throw(_("Annuleer eerst journaalpost {0}.").format(self.journaalpost))

	def vorige(self) -> frappe._dict:
		"""De stand die hiervoor is vastgelegd; de journaalpost boekt het verschil daarmee."""
		rijen = frappe.get_all(
			"Onderhanden Werk",
			filters={"bedrijf": self.bedrijf, "peildatum": ("<", self.peildatum), "docstatus": ("<", 2), "journaalpost": ("is", "set")},
			fields=["name", "te_factureren", "vooruitgefactureerd"],
			order_by="peildatum desc",
			limit=1,
		)
		return rijen[0] if rijen else frappe._dict(te_factureren=0, vooruitgefactureerd=0)

	@frappe.whitelist()
	def maak_journaalpost(self) -> str | None:
		"""Een concept-journaalpost met de mutatie van het onderhanden werk sinds de vorige stand."""
		self.check_permission("write")
		if self.journaalpost and frappe.db.get_value("Journal Entry", self.journaalpost, "docstatus") != 2:
			frappe.throw(_("Er is al een journaalpost: {0}.").format(self.journaalpost))
		from openaec_bouw.boekhouding import vul_schema_aan

		vul_schema_aan(self.bedrijf)
		rekening = {nr: frappe.db.get_value("Account", {"company": self.bedrijf, "account_number": nr}, "name") for nr in (ACTIEF, PASSIEF, MUTATIE)}
		ontbreekt = [nr for nr, naam in rekening.items() if not naam]
		if ontbreekt:
			frappe.throw(_("Het bedrijf mist de rekening(en) {0} voor onderhanden werk.").format(", ".join(ontbreekt)))
		vorige = self.vorige()
		actief = flt(flt(self.te_factureren) - flt(vorige.te_factureren), 2)
		passief = flt(flt(self.vooruitgefactureerd) - flt(vorige.vooruitgefactureerd), 2)
		netto = flt(actief - passief, 2)
		if not actief and not passief:
			return None
		regels = []
		for nummer, bedrag in ((ACTIEF, actief), (PASSIEF, -passief), (MUTATIE, -netto)):
			if bedrag:
				regels.append({"account": rekening[nummer], "debit_in_account_currency": bedrag if bedrag > 0 else 0, "credit_in_account_currency": -bedrag if bedrag < 0 else 0})
		post = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"company": self.bedrijf,
				"posting_date": self.peildatum,
				"voucher_type": "Journal Entry",
				"user_remark": _("Mutatie onderhanden werk {0}").format(self.titel),
				"accounts": regels,
			}
		).insert()
		self.db_set("journaalpost", post.name)
		return post.name
