"""Facturen als UBL 2.1 (NLCIUS, de Nederlandse invulling van EN 16931): uit en in.

- `maak` zet een geboekte verkoopfactuur om in een UBL-factuur (of creditnota) die een opdrachtgever of de overheid
  kan inlezen. Versturen over Peppol zit er nog niet in: het bestand download je en stuur je zelf.
- `inlezen` maakt van een ontvangen UBL-factuur een concept-inkoopfactuur, met het bestand als bijlage. De leverancier
  wordt gezocht op btw-nummer en anders op naam; boeken doet een mens.

Eén btw-categorie per factuur (uit de btw-code van het sjabloon). Het bestand is niet tegen de officiële
validatieregels (schematron) van NLCIUS gehaald; zie de tests voor wat wel bewaakt wordt.
"""

from xml.etree import ElementTree as ET

import frappe
from frappe import _
from frappe.utils import flt, getdate

from openaec_bouw.bank import bestand, iban_klopt, ontleed, schoon_iban

CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NLCIUS = "urn:cen.eu:en16931:2017#compliant#urn:fdc:nen.nl:nlcius:v1.0"
PROFIEL = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

# Btw-code van het sjabloon → categorie van EN 16931 (S gewoon, Z nultarief, AE verlegd, K binnen de EU, G uitvoer).
CATEGORIE = {"V21": "S", "V9": "S", "VOV": "S", "V0": "Z", "VVERL": "AE", "VEU": "K", "VEXP": "G"}
REDEN = {
	"AE": "Btw verlegd",
	"K": "Intracommunautaire levering, artikel 138 Btw-richtlijn",
	"G": "Uitvoer buiten de EU",
}
# Categorie op een ontvangen factuur → btw-code van het inkoopsjabloon (bij S en Z op het tarief).
INKOOPCODE = {"AE": "IVERL", "K": "IEU", "G": "IBUI", "E": "I0", "Z": "I0", "O": "I0"}
EENHEDEN = {"Nos": "C62", "Stuk": "C62", "Stuks": "C62", "Unit": "C62", "Hour": "HUR", "Uur": "HUR", "Day": "DAY", "Dag": "DAY", "Meter": "MTR", "m": "MTR", "m2": "MTK", "m3": "MTQ", "Kg": "KGM", "kg": "KGM", "Litre": "LTR"}

ET.register_namespace("cbc", CBC)
ET.register_namespace("cac", CAC)


def _b(ouder, naam: str, tekst=None, **attrs):
	el = ET.SubElement(ouder, f"{{{CBC}}}{naam}", attrs)
	if tekst is not None:
		el.text = str(tekst)
	return el


def _a(ouder, naam: str):
	return ET.SubElement(ouder, f"{{{CAC}}}{naam}")


def _bedrag(waarde) -> str:
	return f"{flt(waarde, 2):.2f}"


def _land(naam: str | None) -> str:
	return (frappe.db.get_value("Country", naam, "code") or "nl").upper() if naam else "NL"


def _btw_nummer(nummer: str | None) -> str:
	return "".join(str(nummer or "").split()).upper()


def _partij(ouder, naam: str, btw: str, kvk: str, adres: frappe._dict | None):
	partij = _a(ouder, "Party")
	if kvk:
		_b(partij, "EndpointID", kvk, schemeID="0106")
	elif btw:
		_b(partij, "EndpointID", btw, schemeID="9944")
	_b(_a(partij, "PartyName"), "Name", naam)
	post = _a(partij, "PostalAddress")
	if adres:
		if adres.address_line1:
			_b(post, "StreetName", adres.address_line1)
		if adres.address_line2:
			_b(post, "AdditionalStreetName", adres.address_line2)
		if adres.city:
			_b(post, "CityName", adres.city)
		if adres.pincode:
			_b(post, "PostalZone", adres.pincode)
	_b(_a(post, "Country"), "IdentificationCode", _land(adres.country if adres else None))
	if btw:
		belasting = _a(partij, "PartyTaxScheme")
		_b(belasting, "CompanyID", btw)
		_b(_a(belasting, "TaxScheme"), "ID", "VAT")
	rechtspersoon = _a(partij, "PartyLegalEntity")
	_b(rechtspersoon, "RegistrationName", naam)
	if kvk:
		_b(rechtspersoon, "CompanyID", kvk, schemeID="0106")
	return partij


def _adres(naam: str | None) -> frappe._dict | None:
	return frappe.db.get_value("Address", naam, ["address_line1", "address_line2", "city", "pincode", "country"], as_dict=True) if naam else None


def _categorie(factuur) -> tuple[str, float]:
	"""De btw-categorie en het tarief van de factuur: uit de btw-code van het sjabloon, anders uit de btw-regels."""
	tarief = flt(sum(flt(t.rate) for t in factuur.taxes if t.charge_type == "On Net Total"))
	code = None
	if factuur.taxes_and_charges and frappe.db.has_column("Sales Taxes and Charges Template", "btw_code"):
		code = frappe.db.get_value("Sales Taxes and Charges Template", factuur.taxes_and_charges, "btw_code")
	categorie = CATEGORIE.get(code or "") or ("S" if tarief else "Z")
	if categorie == "S" and not tarief:
		categorie = "Z"
	return categorie, (tarief if categorie == "S" else 0.0)


def maak(naam: str) -> bytes:
	"""De UBL-factuur (of creditnota) van verkoopfactuur `naam` als XML."""
	f = frappe.get_doc("Sales Invoice", naam)
	if f.docstatus != 1:
		frappe.throw(_("Alleen een geboekte factuur kan als UBL."))
	credit = bool(f.is_return)
	teken = -1 if credit else 1
	soort = "CreditNote" if credit else "Invoice"
	firma = frappe.db.get_value("Company", f.company, ["company_name", "tax_id", "default_bank_account"], as_dict=True)
	kvk = "".join(c for c in str(frappe.db.get_value("Company", f.company, "kvk_nummer") or "") if c.isdigit()) if frappe.db.has_column("Company", "kvk_nummer") else ""
	categorie, tarief = _categorie(f)

	ruimte = f"urn:oasis:names:specification:ubl:schema:xsd:{soort}-2"
	ET.register_namespace("", ruimte)
	wortel = ET.Element(f"{{{ruimte}}}{soort}")
	_b(wortel, "CustomizationID", NLCIUS)
	_b(wortel, "ProfileID", PROFIEL)
	_b(wortel, "ID", f.name)
	_b(wortel, "IssueDate", getdate(f.posting_date).isoformat())
	if not credit and f.due_date:
		_b(wortel, "DueDate", getdate(f.due_date).isoformat())
	_b(wortel, f"{soort}TypeCode", "381" if credit else "380")
	if f.get("g_bedrag") and not credit:
		g_iban = _g_iban(f.company)
		_b(wortel, "Note", f"Van het factuurbedrag gaat {_bedrag(f.g_bedrag)} {f.currency} naar G-rekening {g_iban}.")
	_b(wortel, "DocumentCurrencyCode", f.currency)
	# NLCIUS wil een kenmerk van de koper; zonder inkoopnummer het factuurnummer zelf.
	_b(wortel, "BuyerReference", f.po_no or f.name)
	if f.po_no:
		_b(_a(wortel, "OrderReference"), "ID", f.po_no)
	if credit and f.return_against:
		_b(_a(_a(wortel, "BillingReference"), "InvoiceDocumentReference"), "ID", f.return_against)

	_partij(_a(wortel, "AccountingSupplierParty"), firma.company_name or f.company, _btw_nummer(f.company_tax_id or firma.tax_id), kvk, _adres(f.company_address))
	_partij(_a(wortel, "AccountingCustomerParty"), f.customer_name or f.customer, _btw_nummer(f.tax_id), "", _adres(f.customer_address))

	rekeningen = [frappe.db.get_value("Bank Account", firma.default_bank_account, "iban")] if firma.default_bank_account else []
	if not rekeningen or not rekeningen[0]:
		eigen = frappe.get_all("Bank Account", filters={"is_company_account": 1, "company": f.company, "disabled": 0, "iban": ("is", "set")}, fields=["iban"], order_by="is_default desc, creation asc", limit=1)
		rekeningen = [eigen[0].iban] if eigen else []
	if f.get("g_bedrag") and not credit:
		rekeningen.append(_g_iban(f.company))
	for iban in rekeningen:
		if iban_klopt(iban):
			betaling = _a(wortel, "PaymentMeans")
			_b(betaling, "PaymentMeansCode", "58")
			_b(betaling, "PaymentID", f.name)
			_b(_a(betaling, "PayeeFinancialAccount"), "ID", schoon_iban(iban))

	netto, btw, totaal = teken * flt(f.net_total), teken * flt(f.total_taxes_and_charges), teken * flt(f.grand_total)

	def categorie_el(ouder, naam: str, met_reden: bool):
		el = _a(ouder, naam)
		_b(el, "ID", categorie)
		_b(el, "Percent", f"{tarief:g}")
		if met_reden and categorie in REDEN:
			_b(el, "TaxExemptionReason", REDEN[categorie])
		_b(_a(el, "TaxScheme"), "ID", "VAT")

	belasting = _a(wortel, "TaxTotal")
	_b(belasting, "TaxAmount", _bedrag(btw), currencyID=f.currency)
	deel = _a(belasting, "TaxSubtotal")
	_b(deel, "TaxableAmount", _bedrag(netto), currencyID=f.currency)
	_b(deel, "TaxAmount", _bedrag(btw), currencyID=f.currency)
	categorie_el(deel, "TaxCategory", True)

	som = _a(wortel, "LegalMonetaryTotal")
	_b(som, "LineExtensionAmount", _bedrag(netto), currencyID=f.currency)
	_b(som, "TaxExclusiveAmount", _bedrag(netto), currencyID=f.currency)
	_b(som, "TaxInclusiveAmount", _bedrag(totaal), currencyID=f.currency)
	_b(som, "PayableAmount", _bedrag(totaal), currencyID=f.currency)

	for nr, regel in enumerate(f.items, start=1):
		lijn = _a(wortel, f"{soort}Line")
		_b(lijn, "ID", nr)
		aantal = teken * flt(regel.qty)
		_b(lijn, "CreditedQuantity" if credit else "InvoicedQuantity", f"{aantal:g}", unitCode=EENHEDEN.get(regel.uom or "", "C62"))
		_b(lijn, "LineExtensionAmount", _bedrag(teken * flt(regel.net_amount)), currencyID=f.currency)
		artikel = _a(lijn, "Item")
		if regel.description and regel.description != regel.item_name:
			_b(artikel, "Description", frappe.utils.strip_html(regel.description)[:500])
		_b(artikel, "Name", regel.item_name or regel.item_code)
		categorie_el(artikel, "ClassifiedTaxCategory", False)
		_b(_a(lijn, "Price"), "PriceAmount", f"{flt(regel.net_rate, 4):.4f}".rstrip("0").rstrip("."), currencyID=f.currency)

	ET.indent(wortel, space=" ")
	return ET.tostring(wortel, encoding="utf-8", xml_declaration=True)


def _g_iban(bedrijf: str) -> str:
	rekening = frappe.db.get_value("Company", bedrijf, "g_rekening") if frappe.db.has_column("Company", "g_rekening") else None
	return schoon_iban(frappe.db.get_value("Bank Account", rekening, "iban")) if rekening else ""


@frappe.whitelist()
def download(factuur: str):
	"""De UBL van een verkoopfactuur als download."""
	frappe.has_permission("Sales Invoice", "read", doc=factuur, throw=True)
	frappe.response.filename = f"{frappe.scrub(factuur)}.xml"
	frappe.response.filecontent = maak(factuur)
	frappe.response.type = "download"
	frappe.response.content_type = "application/xml"


def _t(el, pad: str) -> str:
	gevonden = el.find(pad) if el is not None else None
	return (gevonden.text or "").strip() if gevonden is not None and gevonden.text else ""


def lees(inhoud: bytes | str) -> dict:
	"""Een ontvangen UBL-factuur of -creditnota als gegevens: leverancier, nummers, datums, regels en totalen."""
	wortel = ontleed(inhoud)
	if wortel.tag not in ("Invoice", "CreditNote"):
		frappe.throw(_("Dit is geen UBL-factuur."))
	credit = wortel.tag == "CreditNote"
	partij = wortel.find("AccountingSupplierParty/Party")
	regels = []
	for lijn in wortel.findall("CreditNoteLine" if credit else "InvoiceLine"):
		aantal = flt(_t(lijn, "CreditedQuantity" if credit else "InvoicedQuantity")) or 1
		bedrag = flt(_t(lijn, "LineExtensionAmount"))
		regels.append(
			{
				"naam": _t(lijn, "Item/Name") or _t(lijn, "Item/Description") or _("Factuurregel"),
				"omschrijving": _t(lijn, "Item/Description"),
				"aantal": aantal,
				# De prijs uit het regelbedrag: zo tellen kortingen en een prijs per honderd stuks vanzelf goed mee.
				"prijs": bedrag / aantal,
				"bedrag": bedrag,
				"categorie": _t(lijn, "Item/ClassifiedTaxCategory/ID"),
				"tarief": flt(_t(lijn, "Item/ClassifiedTaxCategory/Percent")),
			}
		)
	return {
		"credit": credit,
		"nummer": _t(wortel, "ID"),
		"datum": _t(wortel, "IssueDate"),
		"vervaldatum": _t(wortel, "DueDate") or _t(wortel, "PaymentMeans/PaymentDueDate"),
		"valuta": _t(wortel, "DocumentCurrencyCode") or "EUR",
		"leverancier": _t(partij, "PartyLegalEntity/RegistrationName") or _t(partij, "PartyName/Name"),
		"btw_nummer": _btw_nummer(_t(partij, "PartyTaxScheme/CompanyID")),
		"iban": schoon_iban(_t(wortel, "PaymentMeans/PayeeFinancialAccount/ID")),
		"inkoopnummer": _t(wortel, "OrderReference/ID"),
		"netto": flt(_t(wortel, "LegalMonetaryTotal/TaxExclusiveAmount")),
		"btw": flt(_t(wortel, "TaxTotal/TaxAmount")),
		"totaal": flt(_t(wortel, "LegalMonetaryTotal/PayableAmount")),
		"regels": regels,
	}


def _leverancier(gegevens: dict) -> str:
	if gegevens["btw_nummer"]:
		for l in frappe.get_all("Supplier", filters={"tax_id": ("is", "set"), "disabled": 0}, fields=["name", "tax_id"]):
			if _btw_nummer(l.tax_id) == gegevens["btw_nummer"]:
				return l.name
	op_naam = frappe.get_all("Supplier", filters={"supplier_name": gegevens["leverancier"], "disabled": 0}, pluck="name", limit=2)
	if len(op_naam) == 1:
		return op_naam[0]
	frappe.throw(
		_("Leverancier {0} (btw-nummer {1}) staat er nog niet in. Maak de leverancier aan met dit btw-nummer en lees de factuur opnieuw in.").format(
			gegevens["leverancier"] or "?", gegevens["btw_nummer"] or "-"
		)
	)


def _inkoopsjabloon(bedrijf: str, categorie: str, tarief: float) -> str | None:
	code = INKOOPCODE.get(categorie) or {21: "I21", 9: "I9", 0: "I0"}.get(round(tarief))
	if not code or not frappe.db.has_column("Purchase Taxes and Charges Template", "btw_code"):
		return None
	return frappe.db.get_value("Purchase Taxes and Charges Template", {"company": bedrijf, "btw_code": code, "disabled": 0}, "name")


def inlezen(inhoud: bytes | str, bedrijf: str | None = None, bestandsnaam: str | None = None) -> dict:
	"""Maakt van een UBL-factuur een concept-inkoopfactuur. Geeft `{factuur, leverancier, totaal, verschil}`;
	`verschil` is wat het totaal in ERPNext afwijkt van het totaal op de factuur (0 als het klopt)."""
	from erpnext.controllers.accounts_controller import get_taxes_and_charges

	gegevens = lees(inhoud)
	if not gegevens["regels"]:
		frappe.throw(_("De factuur heeft geen regels."))
	bedrijf = bedrijf or frappe.defaults.get_user_default("Company") or frappe.get_all("Company", pluck="name", limit=1)[0]
	leverancier = _leverancier(gegevens)
	if gegevens["nummer"] and frappe.db.exists("Purchase Invoice", {"supplier": leverancier, "bill_no": gegevens["nummer"], "docstatus": ("<", 2)}):
		frappe.throw(_("Factuur {0} van {1} staat er al in.").format(gegevens["nummer"], leverancier))
	kosten = frappe.db.get_value("Company", bedrijf, "default_expense_account")
	eenheid = next((e for e in ("Stuk", "Stuks", "Nos", "Unit") if frappe.db.exists("UOM", e)), None)
	teken = -1 if gegevens["credit"] else 1
	eerste = gegevens["regels"][0]
	sjabloon = _inkoopsjabloon(bedrijf, eerste["categorie"], eerste["tarief"])
	factuur = frappe.get_doc(
		{
			"doctype": "Purchase Invoice",
			"company": bedrijf,
			"supplier": leverancier,
			"is_return": 1 if gegevens["credit"] else 0,
			"posting_date": gegevens["datum"] or frappe.utils.today(),
			"set_posting_time": 1,
			"bill_no": gegevens["nummer"],
			"bill_date": gegevens["datum"] or None,
			"due_date": max(getdate(gegevens["vervaldatum"] or gegevens["datum"] or None), getdate(gegevens["datum"] or None)),
			"currency": gegevens["valuta"],
			"taxes_and_charges": sjabloon,
			"taxes": get_taxes_and_charges("Purchase Taxes and Charges Template", sjabloon) if sjabloon else [],
			"items": [
				{
					"item_name": r["naam"][:140],
					"description": r["omschrijving"] or r["naam"],
					"qty": teken * r["aantal"],
					"rate": r["prijs"],
					"uom": eenheid,
					"stock_uom": eenheid,
					"conversion_factor": 1,
					"expense_account": kosten,
				}
				for r in gegevens["regels"]
			],
		}
	)
	factuur.insert()
	verschil = flt(abs(flt(factuur.grand_total)) - abs(gegevens["totaal"]), 2) if gegevens["totaal"] else 0
	if verschil:
		factuur.add_comment("Comment", _("Het totaal wijkt {0} af van het totaal op de UBL-factuur ({1}). Loop de regels en de btw na.").format(verschil, gegevens["totaal"]))
	if not sjabloon:
		factuur.add_comment("Comment", _("Er is geen btw-sjabloon gevonden bij deze factuur; kies het zelf."))
	frappe.get_doc(
		{
			"doctype": "File",
			"file_name": bestandsnaam or f"{frappe.scrub(gegevens['nummer'] or factuur.name)}.xml",
			"attached_to_doctype": "Purchase Invoice",
			"attached_to_name": factuur.name,
			"content": inhoud if isinstance(inhoud, bytes) else inhoud.encode("utf-8"),
			"is_private": 1,
		}
	).insert(ignore_permissions=True)
	return {"factuur": factuur.name, "leverancier": leverancier, "totaal": flt(factuur.grand_total, 2), "verschil": verschil}


@frappe.whitelist(methods=["POST"])
def inlezen_bestand(file_url: str, bedrijf: str | None = None) -> dict:
	"""Voor de knop op de lijst met inkoopfacturen: leest een geüpload UBL-bestand in."""
	frappe.has_permission("Purchase Invoice", "create", throw=True)
	inhoud = bestand(file_url)
	if isinstance(inhoud, str):
		inhoud = inhoud.encode("utf-8")
	return inlezen(inhoud, bedrijf)
