"""SEPA-betaalbestand (pain.001.001.09) van openstaande inkoopfacturen, met de G-rekening erin.

Eén bestand is één verzamelopdracht vanaf één eigen bankrekening. Per factuur staat er één overboeking in, of twee
als een deel naar de G-rekening van de leverancier gaat. Het kenmerk (EndToEndId) is het factuurnummer: daarmee
lettert het bankafschrift de betaling later vanzelf af (`bank.letter_af`).

De factuur wordt hier niet als betaald geboekt; dat gebeurt als de afschrijving op het afschrift staat. Wel onthoudt
de factuur in welk bestand hij zat (`sepa_bestand`), zodat hij niet twee keer in een bestand komt.
"""

import json
import re
from xml.etree import ElementTree as ET

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, today

from openaec_bouw.bank import iban_klopt, schoon_iban

NS = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"
# De tekens die een bank in een SEPA-bestand aanneemt; de rest wordt een spatie.
TOEGESTAAN = re.compile(r"[^A-Za-z0-9/\-?:().,'+ ]")


def _el(ouder, naam: str, tekst=None, **attrs):
	el = ET.SubElement(ouder, naam, attrs)
	if tekst is not None:
		el.text = str(tekst)
	return el


def _veilig(tekst: str | None, lengte: int) -> str:
	import unicodedata

	plat = unicodedata.normalize("NFKD", str(tekst or "")).encode("ascii", "ignore").decode()
	return re.sub(r"\s+", " ", TOEGESTAAN.sub(" ", plat)).strip()[:lengte]


def _bedrag(waarde) -> str:
	return f"{flt(waarde, 2):.2f}"


def iban_van_leverancier(leverancier: str) -> str:
	"""Het IBAN van de standaardbankrekening van de leverancier (anders de eerste die er is)."""
	rekeningen = frappe.get_all(
		"Bank Account",
		filters={"party_type": "Supplier", "party": leverancier, "disabled": 0, "iban": ("is", "set")},
		fields=["iban"],
		order_by="is_default desc, creation asc",
		limit=1,
	)
	return schoon_iban(rekeningen[0].iban) if rekeningen else ""


def opdrachten(facturen: list[str], opnieuw: bool = False) -> list[dict]:
	"""De overboekingen voor deze inkoopfacturen: `[{factuur, kenmerk, naam, iban, bedrag, omschrijving}]`.
	Weigert met een duidelijke melding wat niet betaald kan worden."""
	uit, fouten, bedrijven = [], [], set()
	for naam in facturen:
		f = frappe.db.get_value(
			"Purchase Invoice",
			naam,
			["name", "docstatus", "company", "supplier", "supplier_name", "outstanding_amount", "currency", "bill_no", "on_hold", "g_bedrag", "sepa_bestand"],
			as_dict=True,
		)
		if not f or f.docstatus != 1:
			fouten.append(_("{0}: niet geboekt").format(naam))
			continue
		open_ = flt(f.outstanding_amount, 2)
		if open_ <= 0:
			fouten.append(_("{0}: er staat niets open").format(naam))
		elif f.currency != "EUR":
			fouten.append(_("{0}: alleen facturen in euro").format(naam))
		elif f.on_hold:
			fouten.append(_("{0}: de factuur is geblokkeerd").format(naam))
		elif f.sepa_bestand and not opnieuw:
			fouten.append(_("{0}: zit al in betaalbestand {1}").format(naam, f.sepa_bestand))
		else:
			bedrijven.add(f.company)
			iban = iban_van_leverancier(f.supplier)
			g = min(flt(f.g_bedrag, 2), open_)
			g_iban = schoon_iban(frappe.db.get_value("Supplier", f.supplier, "g_rekening_iban")) if g else ""
			if not iban_klopt(iban) and open_ - g > 0:
				fouten.append(_("{0}: leverancier {1} heeft geen geldig IBAN").format(naam, f.supplier_name))
			elif g and not iban_klopt(g_iban):
				fouten.append(_("{0}: leverancier {1} heeft geen geldig IBAN van de G-rekening").format(naam, f.supplier_name))
			else:
				nummer = _veilig(f.bill_no or f.name, 100)
				if open_ - g > 0:
					uit.append({"factuur": f.name, "kenmerk": f.name[:35], "naam": f.supplier_name, "iban": iban, "bedrag": flt(open_ - g, 2), "omschrijving": f"Factuur {nummer}"})
				if g:
					uit.append({"factuur": f.name, "kenmerk": f"{f.name[:33]}-G", "naam": f.supplier_name, "iban": g_iban, "bedrag": g, "omschrijving": f"Factuur {nummer} G-rekening"})
	if len(bedrijven) > 1:
		fouten.append(_("De facturen zijn van meer dan één bedrijf; maak per bedrijf een bestand."))
	if fouten:
		frappe.throw("<br>".join(fouten), title=_("Het betaalbestand is niet gemaakt"))
	if not uit:
		frappe.throw(_("Er zijn geen facturen gekozen."))
	return uit


def maak(bankrekening: str, regels: list[dict], datum=None, kenmerk: str | None = None) -> tuple[str, bytes]:
	"""Het bestand voor deze overboekingen vanaf de eigen `bankrekening`: `(kenmerk van het bestand, XML)`."""
	eigen = frappe.db.get_value("Bank Account", bankrekening, ["iban", "company", "is_company_account", "branch_code"], as_dict=True)
	if not eigen or not eigen.is_company_account:
		frappe.throw(_("Kies een eigen bankrekening."))
	if not iban_klopt(eigen.iban):
		frappe.throw(_("Bankrekening {0} heeft geen geldig IBAN.").format(bankrekening))
	datum = getdate(datum or today())
	if datum < getdate(today()):
		frappe.throw(_("De betaaldatum ligt in het verleden."))
	nu = now_datetime()
	kenmerk = kenmerk or f"OAB-{nu:%Y%m%d-%H%M%S}"
	totaal = _bedrag(sum(r["bedrag"] for r in regels))
	firma = _veilig(frappe.db.get_value("Company", eigen.company, "company_name") or eigen.company, 70)

	wortel = ET.Element("Document", {"xmlns": NS})
	opdracht = _el(wortel, "CstmrCdtTrfInitn")
	kop = _el(opdracht, "GrpHdr")
	_el(kop, "MsgId", kenmerk)
	_el(kop, "CreDtTm", nu.strftime("%Y-%m-%dT%H:%M:%S"))
	_el(kop, "NbOfTxs", len(regels))
	_el(kop, "CtrlSum", totaal)
	_el(_el(kop, "InitgPty"), "Nm", firma)

	partij = _el(opdracht, "PmtInf")
	_el(partij, "PmtInfId", f"{kenmerk}-1")
	_el(partij, "PmtMtd", "TRF")
	_el(partij, "BtchBookg", "true")
	_el(partij, "NbOfTxs", len(regels))
	_el(partij, "CtrlSum", totaal)
	_el(_el(_el(partij, "PmtTpInf"), "SvcLvl"), "Cd", "SEPA")
	_el(_el(partij, "ReqdExctnDt"), "Dt", datum.isoformat())
	_el(_el(partij, "Dbtr"), "Nm", firma)
	_el(_el(_el(partij, "DbtrAcct"), "Id"), "IBAN", schoon_iban(eigen.iban))
	bank = _el(_el(partij, "DbtrAgt"), "FinInstnId")
	bic = re.sub(r"\s+", "", eigen.branch_code or "").upper()
	if re.fullmatch(r"[A-Z0-9]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?", bic):
		_el(bank, "BICFI", bic)
	else:
		_el(_el(bank, "Othr"), "Id", "NOTPROVIDED")
	_el(partij, "ChrgBr", "SLEV")
	for r in regels:
		tx = _el(partij, "CdtTrfTxInf")
		_el(_el(tx, "PmtId"), "EndToEndId", _veilig(r["kenmerk"], 35))
		_el(_el(tx, "Amt"), "InstdAmt", _bedrag(r["bedrag"]), Ccy="EUR")
		_el(_el(tx, "Cdtr"), "Nm", _veilig(r["naam"], 70))
		_el(_el(_el(tx, "CdtrAcct"), "Id"), "IBAN", r["iban"])
		_el(_el(tx, "RmtInf"), "Ustrd", _veilig(r["omschrijving"], 140))
	ET.indent(wortel, space=" ")
	return kenmerk, ET.tostring(wortel, encoding="utf-8", xml_declaration=True)


@frappe.whitelist(methods=["POST"])
def betaalbestand(facturen: str | list, bankrekening: str, datum: str | None = None, opnieuw: bool | int = False) -> dict:
	"""Voor de lijst met inkoopfacturen: het betaalbestand van de gekozen facturen. Geeft
	`{naam, inhoud, aantal, totaal}`; de browser slaat het op."""
	frappe.only_for(["Accounts Manager", "Accounts User", "System Manager"])
	if isinstance(facturen, str):
		facturen = json.loads(facturen)
	facturen = list(dict.fromkeys(str(f) for f in facturen))
	for naam in facturen:
		frappe.has_permission("Purchase Invoice", "write", doc=naam, throw=True)
	frappe.has_permission("Bank Account", "read", doc=bankrekening, throw=True)
	regels = opdrachten(facturen, opnieuw=bool(int(opnieuw or 0)))
	bedrijf = frappe.db.get_value("Purchase Invoice", facturen[0], "company")
	if frappe.db.get_value("Bank Account", bankrekening, "company") != bedrijf:
		frappe.throw(_("De bankrekening is van een ander bedrijf dan de facturen."))
	kenmerk, xml = maak(bankrekening, regels, datum)
	for naam in {r["factuur"] for r in regels}:
		frappe.db.set_value("Purchase Invoice", naam, "sepa_bestand", kenmerk, update_modified=False)
	return {"naam": f"{kenmerk}.xml", "inhoud": xml.decode("utf-8"), "aantal": len(regels), "totaal": flt(sum(r["bedrag"] for r in regels), 2)}


def vul_g_bedrag(doc, method=None) -> None:
	"""Inkoopfactuur (validate): het afgesproken deel naar de G-rekening op een nieuwe factuur, als de leverancier een
	percentage heeft. Wie zelf een bedrag invult of het daarna leegmaakt, houdt dat."""
	if not doc.meta.has_field("g_bedrag"):
		return
	if doc.is_new() and not flt(doc.g_bedrag) and doc.supplier and not doc.is_return:
		pct = flt(frappe.db.get_value("Supplier", doc.supplier, "g_percentage"))
		if pct:
			doc.g_bedrag = flt(flt(doc.net_total) * pct / 100, 2)
	if flt(doc.g_bedrag) < 0 or flt(doc.g_bedrag) > flt(doc.grand_total) + 0.005:
		frappe.throw(_("Het bedrag naar de G-rekening is hoger dan de factuur."))


def controleer_g_verkoop(doc, method=None) -> None:
	"""Verkoopfactuur (validate): een G-bedrag kan alleen als het bedrijf een G-rekening heeft, en niet hoger dan de factuur."""
	if not doc.meta.has_field("g_bedrag") or not flt(doc.g_bedrag):
		return
	if flt(doc.g_bedrag) < 0 or flt(doc.g_bedrag) > flt(doc.grand_total) + 0.005:
		frappe.throw(_("Het bedrag naar de G-rekening is hoger dan de factuur."))
	if not frappe.db.get_value("Company", doc.company, "g_rekening"):
		frappe.throw(_("Vul eerst de G-rekening in bij het bedrijf {0}.").format(doc.company))
