"""Onderhanden werk: de stand per project, het genomen resultaat, het verlies meteen, en de journaalpost met de mutatie."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from openaec_bouw import boekhouding, profiel


class TestOnderhandenWerk(IntegrationTestCase):
	def setUp(self):
		if not frappe.db.count("Company"):
			self.skipTest("ERPNext is op deze site niet ingericht (geen bedrijf)")
		frappe.set_user("Administrator")
		boekhouding.zorg_voor_velden()

	def tearDown(self):
		profiel.draai_terug()

	def _bedrijf(self) -> frappe._dict:
		naam, afkorting = "Ohwtest " + frappe.generate_hash(length=5), "O" + frappe.generate_hash(length=4).upper()
		frappe.get_doc({"doctype": "Company", "company_name": naam, "abbr": afkorting, "country": "Netherlands", "default_currency": "EUR", "chart_of_accounts": "Standard"}).insert()
		boekhouding.zet_rekeningschema(naam)
		return frappe._dict(name=naam, abbr=afkorting)

	def _project(self, bedrijf, aanneemsom, begroot) -> str:
		return (
			frappe.get_doc(
				{"doctype": "Project", "project_name": "Ohw " + frappe.generate_hash(length=6), "company": bedrijf.name, "expected_start_date": add_days(today(), -60), "expected_end_date": add_days(today(), 60), "estimated_costing": begroot, "aanneemsom": aanneemsom}
			)
			.insert()
			.name
		)

	def _factuur(self, doctype, bedrijf, project, bedrag):
		artikel = "Bouwprofiel testartikel"
		if not frappe.db.exists("Item", artikel):
			groep = frappe.get_all("Item Group", filters={"is_group": 0}, pluck="name", limit=1)[0]
			frappe.get_doc({"doctype": "Item", "item_code": artikel, "item_group": groep, "stock_uom": "Nos", "is_stock_item": 0}).insert()
		partij = {"Sales Invoice": ("customer", "Customer", "customer_name"), "Purchase Invoice": ("supplier", "Supplier", "supplier_name")}[doctype]
		naam = "Bouwprofiel test " + partij[1]
		if not frappe.db.exists(partij[1], naam):
			frappe.get_doc({"doctype": partij[1], partij[2]: naam}).insert()
		factuur = frappe.get_doc(
			{
				"doctype": doctype,
				"company": bedrijf.name,
				partij[0]: naam,
				"posting_date": add_days(today(), -10),
				"set_posting_time": 1,
				"due_date": add_days(today(), 30),
				"bill_no": frappe.generate_hash(length=8),
				"currency": "EUR",
				"conversion_rate": 1,
				"items": [{"item_code": artikel, "qty": 1, "rate": bedrag, "project": project}],
			}
		)
		factuur.insert()
		factuur.submit()
		return factuur

	def test_stand_en_journaalpost(self):
		bedrijf = self._bedrijf()
		# A: op schema, halverwege, minder gefactureerd dan gemaakt. B: verlieslatend en vooruit gefactureerd.
		a = self._project(bedrijf, aanneemsom=100000, begroot=80000)
		b = self._project(bedrijf, aanneemsom=50000, begroot=60000)
		self._factuur("Purchase Invoice", bedrijf, a, 40000)
		self._factuur("Sales Invoice", bedrijf, a, 30000)
		self._factuur("Purchase Invoice", bedrijf, b, 15000)
		self._factuur("Sales Invoice", bedrijf, b, 25000)

		stand = frappe.get_doc({"doctype": "Onderhanden Werk", "bedrijf": bedrijf.name, "peildatum": today(), "methode": "Naar voortgang"}).insert()
		regels = {r.project: r for r in stand.regels}
		# A: voortgang 50%, verwacht resultaat 20.000, genomen 10.000, saldo 40.000 + 10.000 - 30.000.
		self.assertEqual((regels[a].voortgang, regels[a].verwacht_resultaat, regels[a].genomen_resultaat, regels[a].saldo), (50, 20000, 10000, 20000))
		# B: verwacht verlies 10.000 wordt meteen genomen, saldo 15.000 - 10.000 - 25.000.
		self.assertEqual((regels[b].verwacht_resultaat, regels[b].genomen_resultaat, regels[b].saldo), (-10000, -10000, -20000))
		self.assertEqual((stand.te_factureren, stand.vooruitgefactureerd, stand.genomen_resultaat), (20000, 20000, 0))

		# Bij oplevering: geen winst vooraf, het verlies wel.
		stand.methode = "Bij oplevering"
		stand.save()
		regels = {r.project: r for r in stand.regels}
		self.assertEqual((regels[a].genomen_resultaat, regels[a].saldo, regels[b].genomen_resultaat), (0, 10000, -10000))

		# Eén stand per bedrijf per peildatum.
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "Onderhanden Werk", "bedrijf": bedrijf.name, "peildatum": today()}).insert()

		post = frappe.get_doc("Journal Entry", stand.maak_journaalpost())
		boeking = {frappe.db.get_value("Account", r.account, "account_number"): (r.debit_in_account_currency, r.credit_in_account_currency) for r in post.accounts}
		# Actief 10.000 debet, passief 20.000 credit, het verschil (een last van 10.000) op de mutatierekening.
		self.assertEqual(boeking, {"3100": (10000, 0), "3110": (0, 20000), "8090": (10000, 0)})
		with self.assertRaises(frappe.ValidationError):
			stand.maak_journaalpost()

	def test_concept_houdt_vastleggen_tegen(self):
		bedrijf = self._bedrijf()
		project = self._project(bedrijf, aanneemsom=10000, begroot=8000)
		self._factuur("Purchase Invoice", bedrijf, project, 2000)
		concept = frappe.get_doc(
			{"doctype": "Sales Invoice", "company": bedrijf.name, "customer": "Bouwprofiel test Customer" if frappe.db.exists("Customer", "Bouwprofiel test Customer") else frappe.get_doc({"doctype": "Customer", "customer_name": "Bouwprofiel test Customer"}).insert().name, "posting_date": add_days(today(), -5), "set_posting_time": 1, "due_date": add_days(today(), 30), "currency": "EUR", "conversion_rate": 1, "items": [{"item_code": "Bouwprofiel testartikel", "qty": 1, "rate": 1000, "project": project}]}
		).insert()
		stand = frappe.get_doc({"doctype": "Onderhanden Werk", "bedrijf": bedrijf.name, "peildatum": today(), "concepten_meetellen": 1}).insert()
		self.assertEqual(stand.gefactureerd, 1000)
		with self.assertRaises(frappe.ValidationError):
			stand.submit()
		stand.reload()
		frappe.delete_doc("Sales Invoice", concept.name)
		stand.submit()
		self.assertEqual((stand.docstatus, stand.gefactureerd, stand.kosten), (1, 0, 2000))
