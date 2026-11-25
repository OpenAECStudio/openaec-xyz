"""Het doctype Btw-aangifte: cijfers uit het rapport, geen overlap, niet indienen met concepten, en de journaalpost."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_first_day, get_last_day, today

from openaec_bouw import boekhouding, profiel


class TestBtwAangifteDocument(IntegrationTestCase):
	def setUp(self):
		if not frappe.db.count("Company"):
			self.skipTest("ERPNext is op deze site niet ingericht (geen bedrijf)")
		frappe.set_user("Administrator")
		boekhouding.zorg_voor_velden()

	def tearDown(self):
		profiel.draai_terug()

	def _bedrijf(self) -> frappe._dict:
		naam, afkorting = "Aangiftetest " + frappe.generate_hash(length=5), "A" + frappe.generate_hash(length=4).upper()
		frappe.get_doc({"doctype": "Company", "company_name": naam, "abbr": afkorting, "country": "Netherlands", "default_currency": "EUR", "chart_of_accounts": "Standard"}).insert()
		boekhouding.zet_rekeningschema(naam)
		return frappe._dict(name=naam, abbr=afkorting)

	def _factuur(self, bedrijf, boeken: bool = True):
		artikel, klant = "Bouwprofiel testartikel", "Bouwprofiel test Customer"
		if not frappe.db.exists("Item", artikel):
			groep = frappe.get_all("Item Group", filters={"is_group": 0}, pluck="name", limit=1)[0]
			frappe.get_doc({"doctype": "Item", "item_code": artikel, "item_group": groep, "stock_uom": "Nos", "is_stock_item": 0}).insert()
		if not frappe.db.exists("Customer", klant):
			frappe.get_doc({"doctype": "Customer", "customer_name": klant}).insert()
		sjabloon = f"BTW 21% - {bedrijf.abbr}"
		factuur = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": bedrijf.name,
				"customer": klant,
				"posting_date": today(),
				"due_date": add_days(today(), 30),
				"currency": "EUR",
				"conversion_rate": 1,
				"taxes_and_charges": sjabloon,
				"taxes": [{k: v for k, v in r.items() if k != "name"} for r in frappe.get_doc("Sales Taxes and Charges Template", sjabloon).as_dict()["taxes"]],
				"items": [{"item_code": artikel, "qty": 1, "rate": 1000}],
			}
		).insert()
		if boeken:
			factuur.submit()
		return factuur

	def _aangifte(self, bedrijf, **extra):
		return frappe.get_doc({"doctype": "Btw-aangifte", "bedrijf": bedrijf.name, "van": get_first_day(today()), "tot": get_last_day(today()), **extra})

	def test_cijfers_overlap_en_indienen(self):
		bedrijf = self._bedrijf()
		self._factuur(bedrijf)
		concept = self._factuur(bedrijf, boeken=False)

		aangifte = self._aangifte(bedrijf).insert()
		self.assertEqual((aangifte.verschuldigd, aangifte.voorbelasting, aangifte.te_betalen), (210, 0, 210))
		self.assertEqual({r.rubriek: r.omzet for r in aangifte.regels}["1a"], 1000)
		self.assertIn(bedrijf.name, aangifte.titel)

		# Een tweede aangifte over hetzelfde tijdvak kan niet.
		with self.assertRaises(frappe.ValidationError):
			self._aangifte(bedrijf).insert()

		# Met concepten meetellen: de voorlopige stand.
		aangifte.concepten_meetellen = 1
		aangifte.save()
		self.assertEqual(aangifte.te_betalen, 420)

		# Indienen kan niet zolang er een concept in het tijdvak staat.
		with self.assertRaises(frappe.ValidationError):
			aangifte.submit()
		aangifte.reload()
		frappe.delete_doc("Sales Invoice", concept.name)
		aangifte.submit()
		self.assertEqual((aangifte.docstatus, aangifte.te_betalen, aangifte.concepten_meetellen), (1, 210, 0))
		self.assertTrue(aangifte.ingediend_op)

		# De journaalpost boekt de btw-rekening leeg naar Btw-afdracht.
		post = frappe.get_doc("Journal Entry", aangifte.maak_journaalpost())
		regels = {frappe.db.get_value("Account", r.account, "account_number"): (r.debit_in_account_currency, r.credit_in_account_currency) for r in post.accounts}
		self.assertEqual(regels, {"1510": (210, 0), "1590": (0, 210)})
		self.assertEqual(frappe.db.get_value("Btw-aangifte", aangifte.name, "journaalpost"), post.name)
		with self.assertRaises(frappe.ValidationError):
			aangifte.maak_journaalpost()

	def test_dochter_neemt_schema_over(self):
		moeder = self._bedrijf()
		frappe.db.set_value("Company", moeder.name, {"is_group": 1, "allow_account_creation_against_child_company": 1})
		naam, afkorting = "Dochtertest " + frappe.generate_hash(length=5), "D" + frappe.generate_hash(length=4).upper()
		frappe.get_doc({"doctype": "Company", "company_name": naam, "abbr": afkorting, "country": "Netherlands", "default_currency": "EUR", "parent_company": moeder.name}).insert()
		uit = boekhouding.neem_schema_over(naam)
		self.assertEqual(uit["schema"], boekhouding.schema()["naam"])
		dochter = frappe.get_doc("Company", naam)
		self.assertEqual(frappe.db.get_value("Account", dochter.default_receivable_account, ["account_number", "rgs_code"]), ("1310", "BVorDeb"))
		self.assertEqual(frappe.db.get_value("Sales Taxes and Charges Template", f"BTW 21% - {afkorting}", "btw_code"), "V21")
		# Dezelfde rekeningnummers als de moeder: de geconsolideerde rapporten leunen daarop.
		nummers = lambda bedrijf: set(frappe.get_all("Account", filters={"company": bedrijf, "account_number": ("is", "set")}, pluck="account_number"))
		self.assertTrue(nummers(moeder.name) <= nummers(naam))
		# Een bedrijf zonder moeder met ons schema wordt geweigerd.
		with self.assertRaises(frappe.ValidationError):
			boekhouding.neem_schema_over(moeder.name)
