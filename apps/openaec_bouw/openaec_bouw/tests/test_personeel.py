"""Personeel: werkpatroon, opbouw in uren, wissel van cao op 1 januari, feestdagen, verval en verlofaanvragen."""

from datetime import date

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from openaec_bouw import bedrijfsinstellingen, personeel, profiel

SOORT = "Testvakantie in uren"


class TestPersoneel(IntegrationTestCase):
	def setUp(self):
		if "hrms" not in frappe.get_installed_apps():
			self.skipTest("Frappe HR staat niet op deze site")
		if not frappe.db.count("Company"):
			self.skipTest("ERPNext is op deze site niet ingericht (geen bedrijf)")
		frappe.set_user("Administrator")
		personeel.na_migratie()
		self.bedrijf = self._bedrijf()
		if not frappe.db.exists("Leave Type", SOORT):
			frappe.get_doc({"doctype": "Leave Type", "leave_type_name": SOORT, "in_uren": 1}).insert()
		self.cao = self._cao()

	def tearDown(self):
		profiel.draai_terug()

	# --- hulp ---------------------------------------------------------------------------------------------

	def _bedrijf(self) -> str:
		naam = "Personeeltest " + frappe.generate_hash(length=5)
		frappe.get_doc({"doctype": "Company", "company_name": naam, "abbr": "P" + frappe.generate_hash(length=4).upper(), "country": "Netherlands", "default_currency": "EUR", "chart_of_accounts": "Standard"}).insert()
		return naam

	def _cao(self, uren_2026=200, uren_2027=240) -> str:
		naam = "Testcao " + frappe.generate_hash(length=5)
		frappe.get_doc({"doctype": "Cao", "cao_naam": naam, "werknemersgroepen": [{"groep": "UTA"}]}).insert()
		alle_feestdagen = [{"feestdag": d, "vrij": 1, "eens_per_vijf_jaar": int(d == "Bevrijdingsdag")} for d in dict.fromkeys(personeel.FEESTDAG_NAMEN.values())]
		for van, tot, uren in (("2025-01-01", "2026-12-31", uren_2026), ("2027-01-01", None, uren_2027)):
			frappe.get_doc({
				"doctype": "Cao Periode", "cao": naam, "werknemersgroep": "UTA", "status": "Vastgesteld", "geldig_van": van, "geldig_tot": tot,
				"normuren_per_week": 40, "verlofrechten": [{"verlofsoort": SOORT, "uren_per_jaar": uren, "verval": "Zes maanden na het jaar"}],
				"feestdagen": alle_feestdagen,
			}).insert()
		return naam

	def _medewerker(self) -> str:
		gender = frappe.get_all("Gender", pluck="name", limit=1) or [frappe.get_doc({"doctype": "Gender", "gender": "Onbekend"}).insert().name]
		return frappe.get_doc({
			"doctype": "Employee", "first_name": "Test", "last_name": frappe.generate_hash(length=5), "gender": gender[0],
			"date_of_birth": "1990-01-01", "date_of_joining": "2025-01-01", "company": self.bedrijf, "status": "Active",
		}).insert().name

	def _contract(self, medewerker, van, uren=40, tot=None, patroon=None, soort="Onbepaalde tijd"):
		doc = frappe.get_doc({
			"doctype": "Arbeidscontract", "medewerker": medewerker, "soort": soort, "van": van, "tot": tot,
			"uren_per_week": uren, "cao": self.cao, "werknemersgroep": "UTA",
		})
		for dag, u in (patroon or {}).items():
			doc.append("werkpatroon", {"weekdag": dag, "uren": u})
		return doc.insert()

	def _opbouw(self, medewerker, jaar, maand) -> float:
		personeel.opbouw_maand(jaar, maand, medewerker)
		return flt(sum(frappe.get_all("Verlofboeking", filters={"medewerker": medewerker, "soort": "Opbouw", "datum": date(jaar, maand, 28 if maand == 2 else 30 if maand in (4, 6, 9, 11) else 31)}, pluck="uren")), 2)

	# --- tests --------------------------------------------------------------------------------------------

	def test_nieuw_bedrijf_krijgt_instellingen(self):
		doc = frappe.get_doc("Bedrijfsinstellingen", self.bedrijf)
		self.assertEqual(sum(r.uren for r in doc.werkweek), 40)
		self.assertEqual(bedrijfsinstellingen.werkweek(self.bedrijf)["Zaterdag"], 0)

	def test_werkpatroon_parttimer_vrije_vrijdag(self):
		mw = self._medewerker()
		c = self._contract(mw, "2026-01-05", uren=32, patroon={"Maandag": 8, "Dinsdag": 8, "Woensdag": 8, "Donderdag": 8, "Vrijdag": 0})
		self.assertAlmostEqual(c.contractfactor, 0.8)
		self.assertEqual(personeel.uren_op_dag(c, "2026-03-13"), 0)  # vrijdag
		self.assertEqual(personeel.uren_voor_aanvraag(mw, "2026-03-09", "2026-03-13"), 32)

	def test_werkpatroon_voorstel_naar_rato(self):
		c = self._contract(self._medewerker(), "2026-01-05", uren=32)
		self.assertEqual(sum(r.uren for r in c.werkpatroon), 32)

	def test_week_a_en_b(self):
		mw = self._medewerker()
		c = self._contract(mw, "2026-01-05", uren=36, patroon={"Maandag": 8, "Dinsdag": 8, "Woensdag": 8, "Donderdag": 8})
		c.append("werkpatroon", {"week": "A", "weekdag": "Vrijdag", "uren": 8})
		c.save()
		self.assertEqual(personeel.uren_op_dag(c, "2026-01-09"), 8)  # vrijdag in week A
		self.assertEqual(personeel.uren_op_dag(c, "2026-01-16"), 0)  # vrijdag in week B

	def test_opbouw_maand_naar_rato(self):
		mw = self._medewerker()
		self._contract(mw, "2026-01-01", uren=32)
		self.assertAlmostEqual(self._opbouw(mw, 2026, 2), round(200 * 0.8 / 12, 2))

	def test_opbouw_indienst_halverwege(self):
		mw = self._medewerker()
		self._contract(mw, "2026-03-16", uren=32)
		self.assertAlmostEqual(self._opbouw(mw, 2026, 3), round(200 * 0.8 / 12 * 16 / 31, 2), places=1)

	def test_contractwijziging_halverwege_de_maand(self):
		mw = self._medewerker()
		self._contract(mw, "2026-01-01", uren=40, tot="2026-04-15")
		self._contract(mw, "2026-04-16", uren=20)
		verwacht = 200 / 12 * (15 / 30) + 200 * 0.5 / 12 * (15 / 30)
		self.assertAlmostEqual(self._opbouw(mw, 2026, 4), round(verwacht, 2), places=1)

	def test_cao_wissel_op_1_januari(self):
		mw = self._medewerker()
		self._contract(mw, "2026-01-01")
		self.assertAlmostEqual(self._opbouw(mw, 2026, 12), round(200 / 12, 2))
		self.assertAlmostEqual(self._opbouw(mw, 2027, 1), round(240 / 12, 2))

	def test_opnieuw_draaien_vervangt(self):
		mw = self._medewerker()
		self._contract(mw, "2026-01-01")
		self._opbouw(mw, 2026, 5)
		self._opbouw(mw, 2026, 5)
		self.assertEqual(frappe.db.count("Verlofboeking", {"medewerker": mw, "soort": "Opbouw"}), 1)

	def test_feestdagen_uit_de_cao(self):
		periode = personeel.periode_op(self.cao, "UTA", "2027-06-01")
		dagen = {d["omschrijving"]: d["datum"] for d in personeel.vrije_dagen(periode, 2027)}
		self.assertEqual(dagen["Tweede Kerstdag"], date(2027, 12, 26))
		self.assertEqual(dagen["Goede Vrijdag"], date(2027, 3, 26))
		self.assertNotIn("Bevrijdingsdag", dagen)  # 2027 is geen lustrumjaar
		frappe.db.set_value("Cao Feestdag", {"parent": periode, "feestdag": "Goede Vrijdag"}, "vrij", 0)
		frappe.clear_document_cache("Cao Periode", periode)
		self.assertNotIn("Goede Vrijdag", {d["omschrijving"] for d in personeel.vrije_dagen(periode, 2027)})
		self.assertIn("Bevrijdingsdag", {d["omschrijving"] for d in personeel.vrije_dagen(personeel.periode_op(self.cao, "UTA", "2025-06-01"), 2025)})

	def test_kalender_en_aanvraag_over_paasmaandag(self):
		mw = self._medewerker()
		self._contract(mw, "2026-01-01")
		kalender = personeel.maak_kalender(self.bedrijf, 2027, self.cao, "UTA")
		personeel.kalender_vaststellen(kalender.name)
		self.assertTrue(personeel.vrij_op(mw, "2027-03-29"))
		# Week van Tweede Paasdag: maandag is vrij, dus 32 van de 40 uur.
		self.assertEqual(personeel.uren_voor_aanvraag(mw, "2027-03-29", "2027-04-02"), 32)

	def test_verlofaanvraag_in_uren(self):
		mw = self._medewerker()
		self._contract(mw, "2026-01-01", uren=32, patroon={"Maandag": 8, "Dinsdag": 8, "Woensdag": 8, "Donderdag": 8})
		personeel.maak_kalender(self.bedrijf, 2026, self.cao, "UTA")
		personeel.kalender_vaststellen(f"{self.bedrijf} 2026 {self.cao} UTA")
		personeel.boek(mw, SOORT, "Startsaldo", "2026-01-01", 20, reden="Test")
		aanvraag = frappe.get_doc({
			"doctype": "Leave Application", "employee": mw, "leave_type": SOORT, "from_date": "2026-06-08", "to_date": "2026-06-12",
			"status": "Approved", "posting_date": "2026-06-01", "company": self.bedrijf,
		})
		self.assertRaises(frappe.ValidationError, aanvraag.insert)  # 32 uur nodig, 20 beschikbaar
		aanvraag = frappe.get_doc({
			"doctype": "Leave Application", "employee": mw, "leave_type": SOORT, "from_date": "2026-06-08", "to_date": "2026-06-09",
			"status": "Approved", "posting_date": "2026-06-01", "company": self.bedrijf,
		}).insert()
		self.assertEqual(aanvraag.uren, 16)
		aanvraag.submit()
		self.assertEqual(personeel.saldo(mw, SOORT, "2026-06-30")[SOORT], 4)
		aanvraag.cancel()
		self.assertEqual(personeel.saldo(mw, SOORT, "2026-06-30")[SOORT], 20)

	def test_verval_oudste_eerst(self):
		mw = self._medewerker()
		self._contract(mw, "2025-01-01")
		periode = personeel.periode_op(self.cao, "UTA", "2025-06-01")
		personeel.boek(mw, SOORT, "Opbouw", "2025-12-31", 100, opbouwjaar=2025, cao_periode=periode)
		personeel.boek(mw, SOORT, "Opbouw", "2026-03-31", 50, opbouwjaar=2026, cao_periode=periode)
		personeel.boek(mw, SOORT, "Opname", "2026-04-10", -60)
		personeel.verval("2026-07-01")
		vervallen = frappe.get_all("Verlofboeking", filters={"medewerker": mw, "soort": "Verval"}, fields=["uren", "opbouwjaar"])
		self.assertEqual([(v.opbouwjaar, v.uren) for v in vervallen], [(2025, -40)])
		personeel.verval("2026-07-02")  # niet nog eens
		self.assertEqual(frappe.db.count("Verlofboeking", {"medewerker": mw, "soort": "Verval"}), 1)

	def test_handmatige_opbouw_mag_niet(self):
		mw = self._medewerker()
		doc = frappe.get_doc({"doctype": "Verlofboeking", "medewerker": mw, "verlofsoort": SOORT, "soort": "Opbouw", "datum": "2026-01-31", "uren": 10})
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_overlappende_contracten(self):
		mw = self._medewerker()
		self._contract(mw, "2026-01-01")
		self.assertRaises(frappe.ValidationError, self._contract, mw, "2026-06-01")

	def test_stilzwijgend_verlengen(self):
		naam = frappe.get_all("Cao Periode", filters={"cao": self.cao, "geldig_van": "2025-01-01"}, pluck="name")[0]
		periode = frappe.get_doc("Cao Periode", naam)
		frappe.delete_doc("Cao Periode", frappe.get_all("Cao Periode", filters={"cao": self.cao, "geldig_van": "2027-01-01"}, pluck="name")[0])
		periode.stilzwijgend_verlengen = 1
		periode.save()
		personeel.periodes_bijwerken("2027-01-02")
		nieuw = frappe.get_all("Cao Periode", filters={"cao": self.cao, "vorige_periode": naam}, fields=["geldig_van", "geldig_tot", "status"])
		self.assertEqual(len(nieuw), 1)
		self.assertEqual(str(nieuw[0].geldig_van), "2027-01-01")
		self.assertEqual(nieuw[0].status, "Stilzwijgend verlengd")
		self.assertEqual(frappe.db.get_value("Cao Periode", naam, "status"), "Verlopen")

	def test_medewerker_krijgt_contract_en_cao(self):
		mw = self._medewerker()
		c = self._contract(mw, "2026-01-01", tot="2030-12-31", soort="Bepaalde tijd")
		self.assertEqual(frappe.db.get_value("Employee", mw, "huidig_contract"), c.name)
		self.assertEqual(frappe.db.get_value("Employee", mw, "cao"), self.cao)
