"""Het rapport Btw-aangifte: de rubrieken uit geboekte verkoop- en inkoopfacturen."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from openaec_bouw import profiel
from openaec_bouw.openaec_bouw.report.btw_aangifte.btw_aangifte import bereken, execute


class TestBtwAangifte(IntegrationTestCase):
	def setUp(self):
		if not frappe.db.count("Company"):
			self.skipTest("ERPNext is op deze site niet ingericht (geen bedrijf)")
		frappe.set_user("Administrator")
		self.bedrijf = frappe.get_all("Company", fields=["name", "abbr"], order_by="creation asc")[0]
		profiel.zet_module("basis", 1)
		self.voor = bereken(self.bedrijf.name, today(), today())

	def tearDown(self):
		frappe.db.rollback()

	def _rekening(self, root_type: str) -> str:
		return frappe.get_all("Account", filters={"company": self.bedrijf.name, "root_type": root_type, "is_group": 0, "account_type": ("in", ["", None, "Income Account", "Expense Account"])}, pluck="name", limit=1)[0]

	def _artikel(self) -> str:
		code = "Bouwprofiel testartikel"
		if not frappe.db.exists("Item", code):
			groep = frappe.get_all("Item Group", filters={"is_group": 0}, pluck="name", limit=1)[0]
			frappe.get_doc({"doctype": "Item", "item_code": code, "item_group": groep, "stock_uom": "Nos", "is_stock_item": 0}).insert()
		return code

	def _partij(self, doctype: str) -> str:
		naam = f"Bouwprofiel test {doctype}"
		if not frappe.db.exists(doctype, naam):
			veld = "customer_name" if doctype == "Customer" else "supplier_name"
			frappe.get_doc({"doctype": doctype, veld: naam}).insert()
		return naam

	def _factuur(self, doctype: str, bedrag: float, sjabloon: str):
		verkoop = doctype == "Sales Invoice"
		naam = f"{sjabloon} - {self.bedrijf.abbr}"
		regel = {"item_code": self._artikel(), "qty": 1, "rate": bedrag}
		regel["income_account" if verkoop else "expense_account"] = self._rekening("Income" if verkoop else "Expense")
		doc = frappe.get_doc(
			{
				"doctype": doctype,
				"company": self.bedrijf.name,
				"customer" if verkoop else "supplier": self._partij("Customer" if verkoop else "Supplier"),
				"posting_date": today(),
				"due_date": add_days(today(), 30),
				"bill_no": "BP-1",
				"currency": frappe.db.get_value("Company", self.bedrijf.name, "default_currency"),
				"conversion_rate": 1,
				"taxes_and_charges": naam,
				"taxes": frappe.get_doc(f"{doctype.split()[0]} Taxes and Charges Template", naam).as_dict()["taxes"],
				"items": [regel],
			}
		)
		for belasting in doc.taxes:
			belasting.name = None
		doc.insert()
		doc.submit()
		return doc

	def _erbij(self, rubriek: str, veld: str) -> float:
		return round(bereken(self.bedrijf.name, today(), today())[rubriek][veld] - self.voor[rubriek][veld], 2)

	def test_rubrieken(self):
		self._factuur("Sales Invoice", 1000, "BTW 21%")
		self._factuur("Sales Invoice", 200, "BTW 9%")
		self._factuur("Sales Invoice", 300, "BTW verlegd")
		self._factuur("Purchase Invoice", 400, "BTW 21%")
		self._factuur("Purchase Invoice", 500, "BTW verlegd")
		self.assertEqual((self._erbij("1a", "omzet"), self._erbij("1a", "btw")), (1000, 210))
		self.assertEqual((self._erbij("1b", "omzet"), self._erbij("1b", "btw")), (200, 18))
		self.assertEqual(self._erbij("1e", "omzet"), 300)
		# Naar ons verlegd: 21% aangeven in 2a en dezelfde btw aftrekken in 5b.
		self.assertEqual((self._erbij("2a", "omzet"), self._erbij("2a", "btw")), (500, 105))
		self.assertEqual(self._erbij("5a", "btw"), 210 + 18 + 105)
		self.assertEqual(self._erbij("5b", "btw"), 84 + 105)
		self.assertEqual(self._erbij("5c", "btw"), 144)

	def test_rapport(self):
		kolommen, rijen, melding = execute({"company": self.bedrijf.name, "van": today(), "tot": today()})
		self.assertEqual([k["fieldname"] for k in kolommen], ["rubriek", "omschrijving", "omzet", "btw"])
		self.assertEqual([r["rubriek"] for r in rijen], ["1a", "1b", "1c", "1e", "2a", "5a", "5b", "5c"])
		self.assertIn("buitenland", melding)
		with self.assertRaises(frappe.ValidationError):
			execute({"company": self.bedrijf.name, "van": today(), "tot": add_days(today(), -1)})
