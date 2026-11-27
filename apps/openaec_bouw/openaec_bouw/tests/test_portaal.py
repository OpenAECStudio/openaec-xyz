"""Klantenportaal: wie wat mag zien via een link, als klant of als medewerker, en wat er gedeeld is."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from openaec_bouw import portaal

KLANT = "portaalklant@voorbeeld.test"
ANDER = "anderklant@voorbeeld.test"


class TestPortaal(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		portaal.na_migratie()
		self.project = self._project("Portaaltest A")
		self.ander_project = self._project("Portaaltest B")
		for email in (KLANT, ANDER):
			if not frappe.db.exists("User", email):
				frappe.get_doc(
					{"doctype": "User", "email": email, "first_name": email.split("@")[0], "user_type": "Website User", "send_welcome_email": 0}
				).insert(ignore_permissions=True)
		frappe.get_doc({"doctype": "Portaaltoegang", "project": self.project, "email": KLANT.upper(), "rol": "Koper"}).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.form_dict.pop("sleutel", None)
		frappe.db.rollback()

	def _project(self, naam):
		return frappe.get_doc({"doctype": "Project", "project_name": f"{naam} {frappe.generate_hash(length=6)}"}).insert().name

	def test_link_geeft_alleen_dat_project_en_niet_schrijven(self):
		url = portaal.link_maken(self.project, "koper")["url"]
		sleutel = url.rsplit("/", 1)[1]
		self.assertNotEqual(frappe.db.get_value("Portaallink", {"project": self.project}, "sleutel_hash"), sleutel)
		frappe.set_user("Guest")
		t = portaal.toegang(None, sleutel)
		self.assertEqual((t.soort, t.project, t.mag_schrijven), ("link", self.project, False))
		with self.assertRaises(frappe.PermissionError):
			portaal.toegang(self.ander_project, sleutel)
		with self.assertRaises(frappe.PermissionError):
			portaal.toegang(None, sleutel[:-1] + ("A" if sleutel[-1] != "A" else "B"))

	def test_verlopen_of_ingetrokken_link_werkt_niet(self):
		sleutel = portaal.link_maken(self.project)["url"].rsplit("/", 1)[1]
		naam = frappe.db.get_value("Portaallink", {"project": self.project}, "name")
		frappe.db.set_value("Portaallink", naam, "ingetrokken", 1)
		self.assertIsNone(portaal.link_bij(sleutel))
		frappe.db.set_value("Portaallink", naam, {"ingetrokken": 0, "geldig_tot": add_days(today(), -1)})
		self.assertIsNone(portaal.link_bij(sleutel))

	def test_klant_ziet_alleen_eigen_project(self):
		frappe.set_user(KLANT)
		self.assertEqual(portaal.toegang(self.project).soort, "klant")
		self.assertEqual([p.name for p in portaal.mijn_projecten()], [self.project])
		self.assertEqual(frappe.db.get_value("Portaaltoegang", {"email": KLANT}, "gebruiker"), KLANT)
		with self.assertRaises(frappe.PermissionError):
			portaal.toegang(self.ander_project)
		frappe.set_user(ANDER)
		with self.assertRaises(frappe.PermissionError):
			portaal.toegang(self.project)

	def test_medewerker_ziet_als_klant(self):
		self.assertEqual(portaal.toegang(self.project).soort, "bedrijf")

	def test_alleen_gedeelde_fotos_en_mijlpalen_en_geen_berichten_via_link(self):
		taak = frappe.get_doc({"doctype": "Task", "subject": "Fundering", "project": self.project, "zichtbaar_voor_klant": 1}).insert()
		frappe.get_doc({"doctype": "Task", "subject": "Intern overleg", "project": self.project}).insert()
		bestand = frappe.get_doc(
			{"doctype": "File", "file_name": "bouw.png", "content": b"\x89PNG\r\n\x1a\n", "is_private": 1}
		).insert()
		for gedeeld in (1, 0):
			frappe.get_doc(
				{"doctype": "Bouwfoto", "project": self.project, "foto": bestand.file_url, "gedeeld": gedeeld}
			).insert()
		frappe.set_user(KLANT)
		portaal.bericht(self.project, "Wanneer komt de steiger?")
		frappe.set_user("Administrator")
		sleutel = portaal.link_maken(self.project)["url"].rsplit("/", 1)[1]

		frappe.set_user("Guest")
		frappe.form_dict.sleutel = sleutel
		g = portaal.gegevens(portaal.toegang(None, sleutel))
		self.assertEqual([m.subject for m in g.mijlpalen], [taak.subject])
		self.assertEqual(len(g.fotos), 1)
		self.assertIn("sleutel=", g.fotos[0].url)
		self.assertEqual(g.berichten, [])

		frappe.set_user(KLANT)
		g = portaal.gegevens(portaal.toegang(self.project))
		self.assertEqual([b.tekst for b in g.berichten], ["Wanneer komt de steiger?"])
		self.assertTrue(g.berichten[0].van_klant)

	def test_via_link_geen_bericht(self):
		sleutel = portaal.link_maken(self.project)["url"].rsplit("/", 1)[1]
		frappe.set_user("Guest")
		frappe.form_dict.sleutel = sleutel
		with self.assertRaises(frappe.PermissionError):
			portaal.bericht(self.project, "hallo")

	def test_dubbele_toegang_geweigerd(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "Portaaltoegang", "project": self.project, "email": KLANT}).insert()
