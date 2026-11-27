"""Bedrijfsinstellingen: wat een bedrijf instelt voor facturen, inkoop, projecten, planning en pdf's.

Dit stond als 93 eigen velden van Z op het bedrijf zelf. Daar paste het niet: de tabel van het bedrijf heeft een
grens voor één regel, en met ERPNext, Frappe HR en die velden samen ging hij erover ("Row size too large"). Het bedrijf
houdt nu alleen wat een bedrijf ís (naam, KvK, adres, bankrekening); de rest staat hier, één document per bedrijf.

`OUDE_VELDEN` zegt waar elk oud veld van Z heen gaat. De patch in Z gebruikt het om bestaande omgevingen over te zetten.
"""

import frappe

# Oud veld op Company → veld in Bedrijfsinstellingen. Velden die naar de standaard gaan, staan in `NAAR_STANDAARD`.
OUDE_VELDEN = {
	"zapp_filiaal_naam": "filiaalnaam",
	"zapp_code": "code",
	"zapp_gln": "gln",
	"zapp_facturatie_email": "facturatie_email",
	"zapp_standaard_organisatiegegevens_tonen": "organisatiegegevens_tonen",
	"zapp_alternatieve_adrespositie": "alternatieve_adrespositie",
	"zapp_dashboard_notitie": "dashboard_notitie",
	"zapp_administratie": "administratie",
	"zapp_dagboek_inkoop": "dagboek_inkoop",
	"zapp_dagboek_verkoop": "dagboek_verkoop",
	"zapp_factuur_voettekst": "factuur_voettekst",
	"zapp_g_rekening_tekst": "g_rekening_tekst",
	"zapp_n_rekening_tekst": "n_rekening_tekst",
	"zapp_g_rekening_percentage": "g_percentage",
	"zapp_verzamelfactuur_titel": "verzamelfactuur_titel",
	"zapp_factuur_btw_grondslag": "btw_grondslag_tonen",
	"zapp_factuur_bsn_kvk_manurenstaat": "bsn_kvk_op_manurenstaat",
	"zapp_factuur_projomschrijving_overnemen": "projectomschrijving_overnemen",
	"zapp_factuur_pdf_projectnummer": "factuur_projectnummer",
	"zapp_factuur_pdf_projectnaam": "factuur_projectnaam",
	"zapp_factuur_pdf_opleverdatum": "factuur_opleverdatum",
	"zapp_factuur_pdf_werkadres": "factuur_werkadres",
	"zapp_factuur_herinnering_1": "herinnering_1",
	"zapp_factuur_herinnering_2": "herinnering_2",
	"zapp_inkoop_io_naam": "inkooporder_naam",
	"zapp_inkoop_oa_naam": "contract_oa_naam",
	"zapp_inkoop_betalingsafspraak": "betalingsafspraak",
	"zapp_inkoop_ob_io_bijvoegen": "bevestiging_io_bijvoegen",
	"zapp_inkoop_ob_oa_bijvoegen": "bevestiging_oa_bijvoegen",
	"zapp_inkoop_projinfo_io": "projectinfo_io",
	"zapp_inkoop_projinfo_oa": "projectinfo_oa",
	"zapp_inkoop_toon_pnr_uitvoerdersbon": "projectnummer_uitvoerdersbon",
	"zapp_offerte_handtekening_positie": "handtekening_positie",
	"zapp_offerte_ondertekening_positie": "ondertekening_positie",
	"zapp_proj_nummer_type": "projectnummer_soort",
	"zapp_proj_nummer_voorvoegsel": "projectnummer_voorvoegsel",
	"zapp_proj_status_aanmaken": "projectstatus_bij_aanmaken",
	"zapp_proj_auto_adres": "projectadres_automatisch",
	"zapp_proj_categorie_verplicht": "categorie_verplicht",
	"zapp_proj_leverbon_factuurdatum": "leverbon_factuurdatum",
	"zapp_proj_start_eindtijd_uren": "start_eindtijd_bij_uren",
	"zapp_proj_alt_bewakingscode_naam": "andere_naam_bewakingscode",
	"zapp_proj_oplevering_tekst": "opleveringstekst",
	"zapp_ctrl_standopname": "standopname",
	"zapp_ctrl_urenprognose_planning": "urenprognose_uit_planning",
	"zapp_ctrl_prognose_realtime": "prognose_direct_bijwerken",
	"zapp_uurtarief": "uurtarief",
	"zapp_verkoop_uurtarief": "verkoop_uurtarief",
	"zapp_prognose_uurtarief": "prognose_uurtarief",
	"zapp_loonkosten_percentage": "loonkosten_percentage",
	"zapp_planning_starttijd": "planning_starttijd",
	"zapp_planning_eindtijd": "planning_eindtijd",
	"zapp_planning_volledige_dagen": "planning_volledige_dagen",
	"zapp_planning_weken_vooruit": "planning_weken_vooruit",
	"zapp_best_financiele": "bestandstype_financieel",
	"zapp_best_inkoop": "bestandstype_inkoop",
	"zapp_best_kvgm": "bestandstype_kvgm",
	"zapp_best_meerwerk": "bestandstype_meerwerk",
	"zapp_best_offerte": "bestandstype_offerte",
	"zapp_best_oplever": "bestandstype_oplever",
	"zapp_pdf_afvalstaat_titel": "titel_afvalstaat",
	"zapp_pdf_manurenstaat_titel": "titel_manurenstaat",
	"zapp_pdf_materiaalstaat_titel": "titel_materiaalstaat",
	"zapp_pdf_materieelstaat_titel": "titel_materieelstaat",
	"zapp_pdf_land_weergeven": "land_op_pdf",
	"zapp_pdf_pnr_afrekenstaat": "projectnummer_afrekenstaat",
	"zapp_pdf_pnr_manurenstaat": "projectnummer_manurenstaat",
	"zapp_pdf_pnr_oplever": "projectnummer_oplever",
	"zapp_pdf_pnr_uitbesteed": "projectnummer_uitbesteed",
}

# Werden een vinkje; het oude veld was een keuzelijst.
OUDE_KEUZES = {"zapp_factuur_auto_herinneringen": ("automatisch_herinneren", "Inschakelen")}

# Wordt een tabel in plaats van zeven losse velden.
OUDE_TOESLAGEN = {
	"zapp_toeslag_inkooporders": "Inkooporders",
	"zapp_toeslag_leverbonnen": "Leverbonnen",
	"zapp_toeslag_materialen": "Materialen",
	"zapp_toeslag_materieel": "Materieel",
	"zapp_toeslag_onderaanneming": "Onderaanneming",
	"zapp_toeslag_overig": "Overig",
	"zapp_toeslag_werk_uitbesteed": "Werk uitbesteed",
}
OUDE_WERKWEEK = {
	"zapp_kantooruren_maandag": "Maandag",
	"zapp_kantooruren_dinsdag": "Dinsdag",
	"zapp_kantooruren_woensdag": "Woensdag",
	"zapp_kantooruren_donderdag": "Donderdag",
	"zapp_kantooruren_vrijdag": "Vrijdag",
	"zapp_kantooruren_zaterdag": "Zaterdag",
	"zapp_kantooruren_zondag": "Zondag",
}

# Naar de standaard van ERPNext of X: KvK op het bedrijf, IBAN als bankrekening, het adres als adresrecord, de
# vervaltijd als standaardbetaalvoorwaarde van het bedrijf.
NAAR_STANDAARD = ("zapp_kvk", "zapp_iban", "zapp_factuur_vervaltijd", "zapp_straatnaam", "zapp_huisnummer", "zapp_postcode", "zapp_plaats", "zapp_adres")

# Een tabel kost geen ruimte in de regel van het bedrijf; deze blijft tot de btw per filiaal is opgelost.
BLIJFT_OP_BEDRIJF = ("zapp_btw_tarieven",)

WEEKDAGEN = ("Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag")
STANDAARD_WERKWEEK = {"Maandag": 8, "Dinsdag": 8, "Woensdag": 8, "Donderdag": 8, "Vrijdag": 8, "Zaterdag": 0, "Zondag": 0}


def voor(bedrijf: str):
	"""De instellingen van een bedrijf; maakt ze aan als ze er nog niet zijn."""
	if frappe.db.exists("Bedrijfsinstellingen", bedrijf):
		return frappe.get_doc("Bedrijfsinstellingen", bedrijf)
	return maak(bedrijf)


def maak(bedrijf: str, waarden: dict | None = None, werkweek: dict | None = None, toeslagen: dict | None = None):
	doc = frappe.new_doc("Bedrijfsinstellingen")
	doc.bedrijf = bedrijf
	doc.update(waarden or {})
	for dag, uren in (werkweek or STANDAARD_WERKWEEK).items():
		doc.append("werkweek", {"weekdag": dag, "uren": uren})
	for soort, percentage in (toeslagen or {}).items():
		doc.append("toeslagen", {"kostensoort": soort, "percentage": percentage})
	doc.insert(ignore_permissions=True)
	return doc


def nieuw_bedrijf(doc, method=None):
	"""Elk nieuw bedrijf krijgt meteen instellingen, met een werkweek van vijf dagen van acht uur."""
	if not frappe.db.exists("Bedrijfsinstellingen", doc.name):
		maak(doc.name)


def werkweek(bedrijf: str) -> dict:
	"""Uren per weekdag van het bedrijf: het voorstel voor een nieuw arbeidscontract."""
	rijen = frappe.get_all("Werkpatroon Dag", filters={"parenttype": "Bedrijfsinstellingen", "parent": bedrijf}, fields=["weekdag", "uren"])
	return {r.weekdag: r.uren for r in rijen} or dict(STANDAARD_WERKWEEK)


def na_migratie():
	"""Zet de velden van Z over als ze er nog staan; elk bedrijf zonder instellingen krijgt ze."""
	neem_z_over()
	for bedrijf in frappe.get_all("Company", pluck="name"):
		if not frappe.db.exists("Bedrijfsinstellingen", bedrijf):
			maak(bedrijf)


# Bankcode in een Nederlands IBAN (teken 5 tot 8) → naam van de bank.
BANKEN = {
	"ABNA": "ABN AMRO", "ASNB": "ASN Bank", "BUNQ": "bunq", "INGB": "ING", "KNAB": "Knab",
	"RABO": "Rabobank", "RBRB": "RegioBank", "SNSB": "SNS", "TRIO": "Triodos Bank",
}


def neem_z_over():
	"""Zet de 93 velden van Z op het bedrijf over naar Bedrijfsinstellingen en de standaard, en haalt ze weg.

	Doet niets op een omgeving zonder die kolommen. Eerst alles overzetten, dan pas de velden en kolommen weg: gaat er
	iets mis, dan staat alles er nog en probeert de volgende migratie het opnieuw.
	"""
	oud = [k for k in (*OUDE_VELDEN, *OUDE_KEUZES, *OUDE_TOESLAGEN, *OUDE_WERKWEEK, *NAAR_STANDAARD) if frappe.db.has_column("Company", k)]
	if not oud:
		return
	for rij in frappe.db.sql(f"select name, country, {', '.join(f'`{k}`' for k in oud)} from tabCompany", as_dict=True):
		_zet_over(rij)
	for veld in frappe.get_all("Custom Field", filters={"dt": "Company", "fieldname": ("in", oud)}, pluck="name"):
		frappe.delete_doc("Custom Field", veld, ignore_permissions=True, force=True)
	frappe.db.commit()
	frappe.db.sql_ddl(f"alter table tabCompany {', '.join(f'drop column `{k}`' for k in oud)}")
	frappe.clear_cache(doctype="Company")


def _gevuld(waarde) -> bool:
	return waarde not in (None, "")


def _zet_over(rij):
	doc = voor(rij.name)
	for oud, nieuw in OUDE_VELDEN.items():
		if _gevuld(rij.get(oud)):
			doc.set(nieuw, rij[oud])
	for oud, (nieuw, aan) in OUDE_KEUZES.items():
		if _gevuld(rij.get(oud)):
			doc.set(nieuw, int(rij[oud] == aan))
	if any(_gevuld(rij.get(k)) for k in OUDE_WERKWEEK):
		doc.set("werkweek", [{"weekdag": dag, "uren": rij.get(k) or 0} for k, dag in OUDE_WERKWEEK.items()])
	if any(rij.get(k) for k in OUDE_TOESLAGEN):
		doc.set("toeslagen", [{"kostensoort": soort, "percentage": rij[k]} for k, soort in OUDE_TOESLAGEN.items() if rij.get(k)])
	doc.save(ignore_permissions=True)

	if _gevuld(rij.get("zapp_kvk")) and frappe.db.has_column("Company", "kvk_nummer") and not frappe.db.get_value("Company", rij.name, "kvk_nummer"):
		frappe.db.set_value("Company", rij.name, "kvk_nummer", rij.zapp_kvk, update_modified=False)
	if rij.get("zapp_factuur_vervaltijd"):
		_veilig(rij.name, f"vervaltijd {rij.zapp_factuur_vervaltijd} dagen", _betaalvoorwaarde, rij.name, int(rij.zapp_factuur_vervaltijd))
	if _gevuld(rij.get("zapp_iban")):
		_veilig(rij.name, f"IBAN {rij.zapp_iban}", _bankrekening, rij.name, rij.zapp_iban)
	if any(_gevuld(rij.get(k)) for k in ("zapp_straatnaam", "zapp_adres", "zapp_postcode", "zapp_plaats")):
		adres = ", ".join(filter(None, [rij.get("zapp_straatnaam"), rij.get("zapp_huisnummer"), rij.get("zapp_adres"), rij.get("zapp_postcode"), rij.get("zapp_plaats")]))
		_veilig(rij.name, f"adres {adres}", _adres, rij)


def _veilig(bedrijf: str, wat: str, stap, *args):
	"""Een stap naar de standaard mag de migratie niet tegenhouden: lukt hij niet, dan blijft de waarde als opmerking
	op het bedrijf staan, zodat niets verloren gaat."""
	frappe.db.savepoint("z_over")
	try:
		stap(*args)
	except Exception as fout:
		frappe.db.rollback(save_point="z_over")
		frappe.clear_messages()
		frappe.get_doc("Company", bedrijf).add_comment("Comment", f"Uit Z overgezet, maar niet automatisch vastgelegd ({fout}): {wat}")


def _betaalvoorwaarde(bedrijf: str, dagen: int):
	"""De vervaltijd van Z als betaalvoorwaarde "<n> dagen" (zoals in de module basis), standaard voor het bedrijf."""
	if frappe.db.get_value("Company", bedrijf, "payment_terms"):
		return
	naam = f"{dagen} dagen"
	regel = {"invoice_portion": 100, "due_date_based_on": "Day(s) after invoice date", "credit_days": dagen}
	if not frappe.db.exists("Payment Term", naam):
		frappe.get_doc({"doctype": "Payment Term", "payment_term_name": naam, **regel}).insert(ignore_permissions=True)
	if not frappe.db.exists("Payment Terms Template", naam):
		frappe.get_doc({"doctype": "Payment Terms Template", "template_name": naam, "terms": [{"payment_term": naam, **regel}]}).insert(ignore_permissions=True)
	frappe.db.set_value("Company", bedrijf, "payment_terms", naam, update_modified=False)


def _bankrekening(bedrijf: str, iban: str):
	"""Het IBAN van het bedrijf als bankrekening van ERPNext, gekoppeld aan de eerste bankrekening in het grootboek."""
	iban = iban.replace(" ", "").upper()
	if frappe.db.exists("Bank Account", {"iban": iban, "company": bedrijf}):
		return
	grootboek = frappe.db.get_value("Account", {"company": bedrijf, "account_type": "Bank", "is_group": 0}, "name")
	if not grootboek:
		frappe.get_doc("Company", bedrijf).add_comment("Comment", f"IBAN uit Z: {iban}. Geen bankrekening in het grootboek om het aan te koppelen.")
		return
	bank = BANKEN.get(iban[4:8], iban[4:8] or "Bank")
	if not frappe.db.exists("Bank", bank):
		frappe.get_doc({"doctype": "Bank", "bank_name": bank}).insert(ignore_permissions=True)
	frappe.get_doc({
		"doctype": "Bank Account", "account_name": f"{bedrijf} {iban[-4:]}", "bank": bank, "iban": iban,
		"company": bedrijf, "is_company_account": 1, "account": grootboek,
	}).insert(ignore_permissions=True)


def _adres(rij):
	"""Het adres uit Z als adresrecord van het bedrijf, tenzij het er al staat."""
	straat = " ".join(filter(None, [rij.get("zapp_straatnaam"), rij.get("zapp_huisnummer")])) or rij.get("zapp_adres")
	if frappe.db.exists("Address", {"address_line1": straat, "pincode": rij.get("zapp_postcode")}):
		return
	adres = frappe.get_doc({
		"doctype": "Address", "address_title": rij.name, "address_type": "Office", "address_line1": straat or rij.name,
		"pincode": rij.get("zapp_postcode"), "city": rij.get("zapp_plaats") or "-", "country": rij.country or "Netherlands",
		"is_your_company_address": 1, "links": [{"link_doctype": "Company", "link_name": rij.name}],
	})
	adres.insert(ignore_permissions=True)
