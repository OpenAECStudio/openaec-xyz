"""De lader van het bouwprofiel: aanvullen, niet overschrijven, wat de klant weghaalt blijft weg, en een module uitzetten
haalt alleen weg wat ongewijzigd en ongebruikt is."""

import frappe
from frappe.tests import IntegrationTestCase

from openaec_bouw import profiel


class TestProfiel(IntegrationTestCase):
	def setUp(self):
		if not frappe.db.count("Company"):
			self.skipTest("ERPNext is op deze site niet ingericht (geen bedrijf)")
		frappe.set_user("Administrator")
		# Schoon beginnen: alle modules uit (haalt weg wat een eerdere installatie zette).
		for module in profiel.modules():
			profiel.zet_module(module, 0)

	def tearDown(self):
		frappe.db.rollback()

	def test_modules_kloppen(self):
		alle = profiel.modules()
		self.assertLessEqual({"basis", "projecten", "ontwerp", "uitvoering"}, set(alle))
		for module in alle.values():
			self.assertTrue(module["titel"] and module["records"])
			namen = [(r.get("doctype") or r["soort"], r["naam"]) for r in module["records"]]
			self.assertEqual(len(namen), len(set(namen)), f"dubbel record in {module['id']}")

	def test_aanzetten_vult_aan_en_is_idempotent(self):
		uit = profiel.zet_module("projecten", 1)
		self.assertTrue(uit["aan"])
		self.assertGreater(uit["gezet"], 0)
		self.assertTrue(frappe.db.exists("Project Type", "Nieuwbouw"))
		self.assertTrue(frappe.db.exists("Activity Type", "Werkvoorbereiding"))
		self.assertEqual(profiel.pas_toe(), {"projecten": 0})
		stand = {m["id"]: m for m in profiel.stand()}
		self.assertTrue(stand["projecten"]["aan"])
		self.assertEqual(stand["projecten"]["gezet"], uit["gezet"])
		self.assertFalse(stand["uitvoering"]["aan"])

	def test_wat_de_klant_weghaalt_blijft_weg(self):
		profiel.zet_module("projecten", 1)
		frappe.delete_doc("Project Type", "Infra")
		self.assertEqual(profiel.pas_toe(), {"projecten": 0})
		self.assertFalse(frappe.db.exists("Project Type", "Infra"))

	def test_bestaand_record_blijft_van_de_klant(self):
		frappe.get_doc({"doctype": "Project Type", "project_type": "Onderhoud", "description": "van de klant"}).insert()
		profiel.zet_module("projecten", 1)
		self.assertEqual(frappe.db.get_value("Project Type", "Onderhoud", "description"), "van de klant")
		profiel.zet_module("projecten", 0)
		# Niet door de lader gezet: blijft staan.
		self.assertTrue(frappe.db.exists("Project Type", "Onderhoud"))

	def test_uitzetten_laat_gewijzigd_staan(self):
		profiel.zet_module("projecten", 1)
		doc = frappe.get_doc("Project Type", "Intern")
		doc.description = "aangepast door de klant"
		doc.save()
		uit = profiel.zet_module("projecten", 0)
		self.assertFalse(frappe.db.exists("Project Type", "Nieuwbouw"))
		self.assertTrue(frappe.db.exists("Project Type", "Intern"))
		self.assertIn({"doctype": "Project Type", "naam": "Intern", "reden": "gewijzigd"}, uit["gebleven"])
		self.assertEqual(frappe.db.count(profiel.REGEL, {"module": "projecten"}), 0)

	def test_btw_per_bedrijf(self):
		profiel.zet_module("basis", 1)
		bedrijf = frappe.get_all("Company", fields=["name", "abbr"], order_by="creation asc")[0]
		rekening = f"BTW 9% - {bedrijf.abbr}"
		self.assertEqual(frappe.db.get_value("Account", rekening, ["account_type", "tax_rate"]), ("Tax", 9.0))
		for sjabloon in profiel.BTW_SJABLONEN:
			doc = frappe.get_doc(sjabloon, rekening)
			self.assertEqual((doc.company, doc.taxes[0].rate, doc.taxes[0].account_head), (bedrijf.name, 9.0, rekening))
		self.assertTrue(frappe.db.exists("Sales Taxes and Charges Template", f"BTW verlegd - {bedrijf.abbr}"))
		self.assertTrue(frappe.db.exists("Customer Group", "Woningcorporatie"))
		self.assertTrue(frappe.db.exists("Payment Terms Template", "30 dagen"))

	def test_projectsjabloon_met_fasen(self):
		profiel.zet_module("projecten", 1)
		profiel.zet_module("ontwerp", 1)
		sjabloon = frappe.get_doc("Project Template", "Ontwerpproject (SO t/m UO)")
		self.assertEqual([t.subject for t in sjabloon.tasks][:2], ["SO - Schetsontwerp", "VO - Voorlopig ontwerp"])
		self.assertEqual(sjabloon.project_type, "Advies en engineering")
		taken = [frappe.db.get_value("Task", t.task, ["is_template", "start", "duration"]) for t in sjabloon.tasks]
		self.assertEqual(taken[1], (1, 15, 20))
		# Zonder project erop: uitzetten haalt het sjabloon en zijn sjabloontaken weg.
		taaknamen = [t.task for t in sjabloon.tasks]
		profiel.zet_module("ontwerp", 0)
		self.assertFalse(frappe.db.exists("Project Template", sjabloon.name))
		self.assertFalse(frappe.db.exists("Task", taaknamen[0]))

	def test_sjabloon_in_gebruik_blijft(self):
		profiel.zet_module("projecten", 1)
		profiel.zet_module("ontwerp", 1)
		naam = "Ontwerpproject (SO t/m UO)"
		# Een project van het sjabloon krijgt de fasen als taken.
		project = frappe.get_doc(
			{"doctype": "Project", "project_name": "Bouwprofiel test", "project_template": naam, "expected_start_date": "2026-12-01",
				"company": frappe.get_all("Company", pluck="name", order_by="creation asc")[0]}
		).insert()
		self.assertEqual(frappe.db.count("Task", {"project": project.name}), 5)
		uit = profiel.zet_module("ontwerp", 0)
		self.assertTrue(frappe.db.exists("Project Template", naam))
		self.assertIn({"doctype": "Project Template", "naam": naam, "reden": "in gebruik"}, uit["gebleven"])

	def test_onbekende_module(self):
		with self.assertRaises(frappe.ValidationError):
			profiel.zet_module("bestaat-niet", 1)
