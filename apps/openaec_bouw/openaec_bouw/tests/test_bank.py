"""Bank en facturen: CAMT.053 inlezen en afletteren, het SEPA-betaalbestand met de G-rekening, en UBL uit en in."""

from xml.etree import ElementTree as ET

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from openaec_bouw import bank, boekhouding, profiel, sepa, ubl

EIGEN_IBAN = "NL91ABNA0417164300"
G_IBAN = "NL20INGB0001234567"
LEVERANCIER_IBAN = "NL44RABO0123456789"
LEVERANCIER_G_IBAN = "NL69INGB0123456789"
PAIN = {"p": sepa.NS}


def camt(iban: str, regels: list[dict]) -> bytes:
	"""Een klein afschrift: per regel bedrag, bij (True/False), omschrijving, en eventueel kenmerk en id."""
	posten = ""
	for nr, r in enumerate(regels, start=1):
		wie = "Dbtr" if r["bij"] else "Cdtr"
		posten += f"""
   <Ntry>
    <Amt Ccy="EUR">{r["bedrag"]:.2f}</Amt>
    <CdtDbtInd>{"CRDT" if r["bij"] else "DBIT"}</CdtDbtInd>
    <BookgDt><Dt>{today()}</Dt></BookgDt>
    <AcctSvcrRef>{r.get("id", f"REF{nr}")}</AcctSvcrRef>
    <NtryDtls><TxDtls>
     <Refs><EndToEndId>{r.get("kenmerk", "NOTPROVIDED")}</EndToEndId></Refs>
     <RltdPties><{wie}><Nm>Tegenpartij &amp; Zn</Nm></{wie}><{wie}Acct><Id><IBAN>{LEVERANCIER_IBAN}</IBAN></Id></{wie}Acct></RltdPties>
     <RmtInf><Ustrd>{r["omschrijving"]}</Ustrd></RmtInf>
    </TxDtls></NtryDtls>
   </Ntry>"""
	return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
 <BkToCstmrStmt>
  <GrpHdr><MsgId>TEST</MsgId></GrpHdr>
  <Stmt>
   <Id>AFSCHRIFT-1</Id>
   <Acct><Id><IBAN>{iban}</IBAN></Id><Ccy>EUR</Ccy></Acct>{posten}
  </Stmt>
 </BkToCstmrStmt>
</Document>""".encode()


class TestBank(IntegrationTestCase):
	def setUp(self):
		if not frappe.db.count("Company"):
			self.skipTest("ERPNext is op deze site niet ingericht (geen bedrijf)")
		frappe.set_user("Administrator")
		boekhouding.zorg_voor_velden()

	def tearDown(self):
		profiel.draai_terug()

	def _bedrijf(self) -> frappe._dict:
		naam, afkorting = "Banktest " + frappe.generate_hash(length=5), "B" + frappe.generate_hash(length=4).upper()
		frappe.get_doc(
			{"doctype": "Company", "company_name": naam, "abbr": afkorting, "country": "Netherlands", "default_currency": "EUR", "chart_of_accounts": "Standard", "tax_id": "NL123456789B01"}
		).insert()
		boekhouding.zet_rekeningschema(naam)
		if not frappe.db.exists("Bank", "Testbank"):
			frappe.get_doc({"doctype": "Bank", "bank_name": "Testbank"}).insert()
		rekeningen = {}
		for sleutel, nummer, iban in (("bank", "1100", EIGEN_IBAN), ("g", "1150", G_IBAN)):
			grootboek = frappe.db.get_value("Account", {"company": naam, "account_number": nummer}, "name")
			rekeningen[sleutel] = (
				frappe.get_doc(
					{"doctype": "Bank Account", "account_name": f"{sleutel} {afkorting}", "bank": "Testbank", "is_company_account": 1, "company": naam, "account": grootboek, "iban": iban}
				)
				.insert()
				.name
			)
		frappe.db.set_value("Company", naam, {"g_rekening": rekeningen["g"], "kvk_nummer": "12345678", "default_bank_account": rekeningen["bank"]})
		return frappe._dict(name=naam, abbr=afkorting, bank=rekeningen["bank"], g=rekeningen["g"])

	def _artikel(self) -> str:
		artikel = "Bouwprofiel testartikel"
		if not frappe.db.exists("Item", artikel):
			groep = frappe.get_all("Item Group", filters={"is_group": 0}, pluck="name", limit=1)[0]
			frappe.get_doc({"doctype": "Item", "item_code": artikel, "item_group": groep, "stock_uom": "Nos", "is_stock_item": 0}).insert()
		return artikel

	def _verkoop(self, bedrijf, bedrag: float = 1000, **extra):
		klant = "Bouwprofiel test Customer"
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
				"items": [{"item_code": self._artikel(), "qty": 2, "rate": bedrag / 2}],
				**extra,
			}
		)
		factuur.insert()
		factuur.submit()
		return factuur

	def _leverancier(self, **extra) -> str:
		naam = "Onderaannemer " + frappe.generate_hash(length=5)
		leverancier = frappe.get_doc({"doctype": "Supplier", "supplier_name": naam, "tax_id": "NL 8000.11.222.B01", **extra}).insert()
		frappe.get_doc({"doctype": "Bank Account", "account_name": naam, "bank": "Testbank", "party_type": "Supplier", "party": leverancier.name, "iban": LEVERANCIER_IBAN, "is_default": 1}).insert()
		return leverancier.name

	def _inkoop(self, bedrijf, leverancier: str, bedrag: float = 1000, nummer: str = "F2026-0042"):
		factuur = frappe.get_doc(
			{
				"doctype": "Purchase Invoice",
				"company": bedrijf.name,
				"supplier": leverancier,
				"posting_date": today(),
				"due_date": add_days(today(), 30),
				"bill_no": nummer,
				"bill_date": today(),
				"currency": "EUR",
				"conversion_rate": 1,
				"items": [{"item_code": self._artikel(), "qty": 1, "rate": bedrag}],
			}
		)
		factuur.insert()
		factuur.submit()
		return factuur

	def test_iban(self):
		self.assertTrue(bank.iban_klopt("NL91 ABNA 0417 1643 00"))
		self.assertTrue(bank.iban_klopt("de89370400440532013000"))
		self.assertFalse(bank.iban_klopt("NL91ABNA0417164301"))
		self.assertFalse(bank.iban_klopt(""))
		self.assertFalse(bank.iban_klopt("NL91"))

	def test_camt_lezen(self):
		afschrift = bank.lees(camt(EIGEN_IBAN, [{"bedrag": 12.5, "bij": True, "omschrijving": "Factuur 1"}, {"bedrag": 3, "bij": False, "omschrijving": "Kosten", "kenmerk": "ABC"}]))[0]
		self.assertEqual((afschrift["iban"], len(afschrift["regels"])), (EIGEN_IBAN, 2))
		bij, af = afschrift["regels"]
		self.assertEqual((bij["bedrag"], bij["bij"], bij["naam"], bij["tegenrekening"], bij["kenmerk"], bij["id"]), (12.5, True, "Tegenpartij & Zn", LEVERANCIER_IBAN, "", "REF1"))
		self.assertEqual((af["bedrag"], af["bij"], af["kenmerk"], af["omschrijving"]), (3, False, "ABC", "Kosten"))
		with self.assertRaises(frappe.ValidationError):
			bank.lees(b"<Document><Iets/></Document>")
		# Entiteiten van buiten worden niet uitgevoerd.
		with self.assertRaises(frappe.ValidationError):
			bank.lees(b'<?xml version="1.0"?><!DOCTYPE d [<!ENTITY x SYSTEM "file:///etc/passwd">]><Document>&x;</Document>')

	def test_afschrift_lettert_verkoopfactuur_af(self):
		bedrijf = self._bedrijf()
		factuur = self._verkoop(bedrijf)
		bestand = camt(
			EIGEN_IBAN,
			[
				{"bedrag": 1210, "bij": True, "omschrijving": f"Betaling factuur {factuur.name.lower()}"},
				{"bedrag": 55, "bij": True, "omschrijving": "Onbekende storting"},
				{"bedrag": 100, "bij": True, "omschrijving": f"Deel van {factuur.name}"},
			],
		)
		uit = bank.inlezen(bestand)
		self.assertEqual((uit["nieuw"], uit["dubbel"], uit["afgeletterd"], uit["open"]), (3, 0, 1, 2))
		self.assertEqual(frappe.db.get_value("Sales Invoice", factuur.name, "outstanding_amount"), 0)
		transactie = frappe.get_doc("Bank Transaction", {"bank_account": bedrijf.bank, "transaction_id": "REF1"})
		self.assertEqual((transactie.status, transactie.unallocated_amount, len(transactie.payment_entries)), ("Reconciled", 0, 1))
		# Nog eens inlezen maakt niets dubbel.
		uit = bank.inlezen(bestand)
		self.assertEqual((uit["nieuw"], uit["dubbel"]), (0, 3))
		# Een afschrift van een onbekende rekening wordt geweigerd.
		with self.assertRaises(frappe.ValidationError):
			bank.inlezen(camt("NL18RABO0123459876", [{"bedrag": 1, "bij": True, "omschrijving": "x"}]))

	def test_g_rekening_verkoop(self):
		bedrijf = self._bedrijf()
		factuur = self._verkoop(bedrijf, g_bedrag=400)
		# De opdrachtgever betaalt in twee delen: 810 op de bank en 400 op de G-rekening.
		self.assertEqual(bank.inlezen(camt(EIGEN_IBAN, [{"bedrag": 810, "bij": True, "omschrijving": factuur.name}]))["afgeletterd"], 1)
		self.assertEqual(frappe.db.get_value("Sales Invoice", factuur.name, "outstanding_amount"), 400)
		self.assertEqual(bank.inlezen(camt(G_IBAN, [{"bedrag": 400, "bij": True, "omschrijving": factuur.name, "id": "G1"}]))["afgeletterd"], 1)
		self.assertEqual(frappe.db.get_value("Sales Invoice", factuur.name, "outstanding_amount"), 0)
		g_grootboek = frappe.db.get_value("Bank Account", bedrijf.g, "account")
		self.assertEqual(sum(frappe.get_all("GL Entry", filters={"account": g_grootboek, "is_cancelled": 0}, pluck="debit")), 400)
		# Zonder G-rekening bij het bedrijf kan een G-bedrag niet.
		frappe.db.set_value("Company", bedrijf.name, "g_rekening", None)
		with self.assertRaises(frappe.ValidationError):
			self._verkoop(bedrijf, g_bedrag=100)

	def test_sepa_met_g_rekening_en_afletteren(self):
		bedrijf = self._bedrijf()
		leverancier = self._leverancier(g_rekening_iban=LEVERANCIER_G_IBAN, g_percentage=40)
		factuur = self._inkoop(bedrijf, leverancier)
		self.assertEqual(factuur.g_bedrag, 400)
		gewoon = self._inkoop(bedrijf, self._leverancier(), bedrag=250, nummer="2026-7")

		uit = sepa.betaalbestand([factuur.name, gewoon.name], bedrijf.bank, add_days(today(), 1))
		self.assertEqual((uit["aantal"], uit["totaal"]), (3, 1250))
		xml = ET.fromstring(uit["inhoud"])
		self.assertEqual(xml.tag, f"{{{sepa.NS}}}Document")
		self.assertEqual(xml.findtext("p:CstmrCdtTrfInitn/p:GrpHdr/p:CtrlSum", namespaces=PAIN), "1250.00")
		self.assertEqual(xml.findtext("p:CstmrCdtTrfInitn/p:PmtInf/p:DbtrAcct/p:Id/p:IBAN", namespaces=PAIN), EIGEN_IBAN)
		posten = {
			tx.findtext("p:PmtId/p:EndToEndId", namespaces=PAIN): (tx.findtext("p:Amt/p:InstdAmt", namespaces=PAIN), tx.findtext("p:CdtrAcct/p:Id/p:IBAN", namespaces=PAIN))
			for tx in xml.findall("p:CstmrCdtTrfInitn/p:PmtInf/p:CdtTrfTxInf", PAIN)
		}
		self.assertEqual(
			posten,
			{factuur.name: ("600.00", LEVERANCIER_IBAN), f"{factuur.name}-G": ("400.00", LEVERANCIER_G_IBAN), gewoon.name: ("250.00", LEVERANCIER_IBAN)},
		)
		self.assertEqual(frappe.db.get_value("Purchase Invoice", factuur.name, "sepa_bestand"), uit["naam"][:-4])
		# Een factuur komt niet ongemerkt twee keer in een bestand.
		with self.assertRaises(frappe.ValidationError):
			sepa.betaalbestand([factuur.name], bedrijf.bank)
		self.assertEqual(sepa.betaalbestand([factuur.name], bedrijf.bank, opnieuw=1)["aantal"], 2)

		# De afschrijvingen komen terug op het afschrift, met het kenmerk uit het bestand: alles wordt afgeletterd.
		uit = bank.inlezen(
			camt(
				EIGEN_IBAN,
				[
					{"bedrag": 600, "bij": False, "omschrijving": "Factuur F2026-0042", "kenmerk": factuur.name},
					{"bedrag": 400, "bij": False, "omschrijving": "Factuur F2026-0042 G-rekening", "kenmerk": f"{factuur.name}-G"},
					{"bedrag": 250, "bij": False, "omschrijving": "Factuur 2026-7", "kenmerk": gewoon.name},
				],
			)
		)
		self.assertEqual((uit["nieuw"], uit["afgeletterd"]), (3, 3))
		self.assertEqual(frappe.db.get_value("Purchase Invoice", factuur.name, "outstanding_amount"), 0)
		self.assertEqual(frappe.db.get_value("Purchase Invoice", gewoon.name, "outstanding_amount"), 0)

	def test_sepa_weigert_zonder_iban(self):
		bedrijf = self._bedrijf()
		naam = "Zonder bank " + frappe.generate_hash(length=5)
		leverancier = frappe.get_doc({"doctype": "Supplier", "supplier_name": naam}).insert().name
		factuur = self._inkoop(bedrijf, leverancier)
		with self.assertRaises(frappe.ValidationError):
			sepa.betaalbestand([factuur.name], bedrijf.bank)
		self.assertFalse(frappe.db.get_value("Purchase Invoice", factuur.name, "sepa_bestand"))

	def test_ubl_uit_en_in(self):
		bedrijf = self._bedrijf()
		factuur = self._verkoop(bedrijf, g_bedrag=400, po_no="INK-77")
		xml = ubl.maak(factuur.name)
		self.assertIn(b'<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"', xml)
		gegevens = ubl.lees(xml)
		self.assertEqual(
			(gegevens["nummer"], gegevens["credit"], gegevens["netto"], gegevens["btw"], gegevens["totaal"], gegevens["btw_nummer"], gegevens["iban"], gegevens["inkoopnummer"]),
			(factuur.name, False, 1000, 210, 1210, "NL123456789B01", EIGEN_IBAN, "INK-77"),
		)
		self.assertEqual([(r["aantal"], r["prijs"], r["categorie"], r["tarief"]) for r in gegevens["regels"]], [(2, 500, "S", 21)])
		boom = bank.ontleed(xml)
		self.assertEqual(boom.findtext("CustomizationID"), ubl.NLCIUS)
		self.assertEqual([e.text for e in boom.findall("PaymentMeans/PayeeFinancialAccount/ID")], [EIGEN_IBAN, G_IBAN])
		self.assertEqual(boom.findtext("AccountingSupplierParty/Party/PartyLegalEntity/CompanyID"), "12345678")

		# Dezelfde factuur als inkoop inlezen: de leverancier wordt op btw-nummer gevonden, het totaal klopt.
		with self.assertRaises(frappe.ValidationError):
			ubl.inlezen(xml, bedrijf.name)
		leverancier = frappe.get_doc({"doctype": "Supplier", "supplier_name": "Leverancier " + frappe.generate_hash(length=5), "tax_id": "NL123456789B01"}).insert().name
		uit = ubl.inlezen(xml, bedrijf.name)
		self.assertEqual((uit["leverancier"], uit["totaal"], uit["verschil"]), (leverancier, 1210, 0))
		inkoop = frappe.get_doc("Purchase Invoice", uit["factuur"])
		self.assertEqual((inkoop.docstatus, inkoop.bill_no, inkoop.net_total, inkoop.taxes_and_charges), (0, factuur.name, 1000, f"BTW 21% - {bedrijf.abbr}"))
		self.assertTrue(frappe.db.exists("File", {"attached_to_doctype": "Purchase Invoice", "attached_to_name": inkoop.name}))
		# Dezelfde factuur nog eens wordt geweigerd.
		with self.assertRaises(frappe.ValidationError):
			ubl.inlezen(xml, bedrijf.name)

	def test_ubl_creditnota(self):
		from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return

		bedrijf = self._bedrijf()
		factuur = self._verkoop(bedrijf)
		credit = make_sales_return(factuur.name)
		credit.insert()
		credit.submit()
		gegevens = ubl.lees(ubl.maak(credit.name))
		self.assertEqual((gegevens["credit"], gegevens["totaal"], gegevens["regels"][0]["aantal"]), (True, 1210, 2))
