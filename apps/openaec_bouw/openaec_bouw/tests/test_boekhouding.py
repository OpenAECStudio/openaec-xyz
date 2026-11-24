"""De Nederlandse laag op de boekhouding: RGS-codes, het eigen rekeningschema en de auditfile."""

from xml.etree import ElementTree as ET

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from openaec_bouw import auditfile, boekhouding, profiel
from openaec_bouw.openaec_bouw.report.btw_aangifte.btw_aangifte import bereken

NS = {"x": auditfile.NS}


class TestBoekhouding(IntegrationTestCase):
	def setUp(self):
		if not frappe.db.count("Company"):
			self.skipTest("ERPNext is op deze site niet ingericht (geen bedrijf)")
		frappe.set_user("Administrator")
		boekhouding.zorg_voor_velden()

	def tearDown(self):
		profiel.draai_terug()

	def _bedrijf(self) -> frappe._dict:
		naam, afkorting = "Schematest " + frappe.generate_hash(length=5), "S" + frappe.generate_hash(length=4).upper()
		frappe.get_doc(
			{"doctype": "Company", "company_name": naam, "abbr": afkorting, "country": "Netherlands", "default_currency": "EUR", "chart_of_accounts": "Standard"}
		).insert()
		return frappe._dict(name=naam, abbr=afkorting)

	def test_schema_klopt(self):
		gegevens = boekhouding.schema()
		nummers = [r[0] for r in gegevens["rekeningen"]]
		self.assertEqual(len(nummers), len(set(nummers)))
		self.assertTrue(all(r[4] for r in gegevens["rekeningen"]), "elke rekening heeft een RGS-code")
		self.assertTrue(set(gegevens["standaard"].values()) <= set(nummers))
		boom = boekhouding._boom(gegevens["rekeningen"])
		self.assertEqual({v["root_type"] for v in boom.values()}, {"Asset", "Liability", "Equity", "Income", "Expense"})

	def test_rgs_voorstel_vult_alleen_leeg(self):
		bedrijf = frappe.get_all("Company", pluck="name", order_by="creation asc")[0]
		rekening = frappe.get_all("Account", filters={"company": bedrijf, "account_type": "Receivable", "is_group": 0}, pluck="name")[0]
		frappe.db.set_value("Account", rekening, "rgs_code", "EIGEN")
		boekhouding.vul_rgs_aan(bedrijf)
		self.assertEqual(frappe.db.get_value("Account", rekening, "rgs_code"), "EIGEN")
		self.assertFalse(frappe.get_all("Account", filters={"company": bedrijf, "rgs_code": ("is", "not set")}))

	def test_rekeningschema_factuur_en_auditfile(self):
		bedrijf = self._bedrijf()
		uit = boekhouding.zet_rekeningschema(bedrijf.name)
		self.assertEqual(uit["rekeningen"], len([r for r in boekhouding.schema()["rekeningen"] if r[2] is not None]))
		firma = frappe.get_doc("Company", bedrijf.name)
		for veld in ("default_receivable_account", "default_payable_account", "default_income_account", "default_expense_account", "round_off_account", "write_off_account"):
			self.assertTrue(firma.get(veld), veld)
		self.assertEqual(frappe.db.get_value("Account", firma.default_receivable_account, ["account_number", "rgs_code"]), ("1310", "BVorDeb"))
		# De btw-sjablonen hangen aan het nieuwe schema en hebben hun code.
		sjabloon = f"BTW 21% - {bedrijf.abbr}"
		self.assertEqual(frappe.db.get_value("Sales Taxes and Charges Template", sjabloon, "btw_code"), "V21")
		hoofd = frappe.get_doc("Sales Taxes and Charges Template", sjabloon).taxes[0].account_head
		self.assertEqual(frappe.db.get_value("Account", hoofd, "account_number"), "1510")

		# Een factuur boeken moet nu zonder verdere inrichting lukken.
		artikel = "Bouwprofiel testartikel"
		if not frappe.db.exists("Item", artikel):
			groep = frappe.get_all("Item Group", filters={"is_group": 0}, pluck="name", limit=1)[0]
			frappe.get_doc({"doctype": "Item", "item_code": artikel, "item_group": groep, "stock_uom": "Nos", "is_stock_item": 0}).insert()
		klant = "Bouwprofiel test Customer"
		if not frappe.db.exists("Customer", klant):
			frappe.get_doc({"doctype": "Customer", "customer_name": klant}).insert()
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
		)
		factuur.insert()
		factuur.submit()
		cijfers = bereken(bedrijf.name, today(), today())
		self.assertEqual((cijfers["1a"]["omzet"], cijfers["1a"]["btw"]), (1000, 210))

		# Nu er geboekt is, kan het schema niet meer vervangen worden.
		with self.assertRaises(frappe.ValidationError):
			boekhouding.zet_rekeningschema(bedrijf.name)

		boekjaar = frappe.get_all("Fiscal Year", filters={"year_start_date": ("<=", today()), "year_end_date": (">=", today())}, pluck="name")[0]
		xml = ET.fromstring(auditfile.maak(bedrijf.name, boekjaar))
		self.assertEqual(xml.tag, f"{{{auditfile.NS}}}auditfile")
		mutaties = xml.find("x:company/x:transactions", NS)
		debet, credit = mutaties.findtext("x:totalDebit", namespaces=NS), mutaties.findtext("x:totalCredit", namespaces=NS)
		self.assertEqual((debet, credit), ("1210.00", "1210.00"))
		lijnen = mutaties.findall("x:journal/x:transaction/x:trLine", NS)
		self.assertEqual(int(mutaties.findtext("x:linesCount", namespaces=NS)), len(lijnen))
		self.assertEqual({(l.findtext("x:accID", namespaces=NS), l.findtext("x:amntTp", namespaces=NS), l.findtext("x:amnt", namespaces=NS)) for l in lijnen}, {("1310", "D", "1210.00"), ("8010", "C", "1000.00"), ("1510", "C", "210.00")})
		codes = {r.findtext("x:accID", namespaces=NS): r.findtext("x:leadCode", namespaces=NS) for r in xml.findall("x:company/x:generalLedger/x:ledgerAccount", NS)}
		self.assertEqual((codes["1310"], codes["8010"]), ("BVorDeb", "WOmz"))
		self.assertEqual(xml.findtext("x:company/x:customersSuppliers/x:customerSupplier/x:custSupID", namespaces=NS), klant)
		self.assertEqual(len(xml.findall("x:company/x:periods/x:period", NS)), 12)
