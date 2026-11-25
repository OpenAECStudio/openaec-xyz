"""Bank: afschriften inlezen (CAMT.053), IBAN's en de G-rekening.

- `lees` zet een CAMT.053-bestand om in afschriften met regels; `inlezen` maakt er banktransacties van op de
  bankrekening met hetzelfde IBAN. Een regel die er al staat (zelfde kenmerk van de bank) komt er niet nog eens bij.
- Daarna wordt afgeletterd waar het zeker is: het factuurnummer staat in de omschrijving en het bedrag klopt met wat
  openstaat (of, bij een factuur met een G-bedrag, met een van de twee delen). De rest blijft open voor het
  afstemscherm van ERPNext; daar gelden ook de eigen afletterregels (Bank Transaction Rule).
- De G-rekening is een gewone bankrekening met een eigen grootboekrekening: het afschrift ervan lees je net zo in.
"""

import hashlib
import re

import frappe
from defusedxml import ElementTree as ET
from frappe import _
from frappe.utils import flt, getdate

MAX_BESTAND = 20 * 1024 * 1024


def schoon_iban(iban: str | None) -> str:
	return re.sub(r"\s+", "", str(iban or "")).upper()


def iban_klopt(iban: str | None) -> bool:
	"""De controle van ISO 13616: lengte, tekens en de rest bij delen door 97."""
	iban = schoon_iban(iban)
	if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", iban):
		return False
	return int("".join(str(int(t, 36)) for t in iban[4:] + iban[:4])) % 97 == 1


def ontleed(inhoud: bytes | str):
	"""XML van buiten: zonder entiteiten (defusedxml) en zonder naamruimten, zodat elke versie van een schema leest."""
	if isinstance(inhoud, str):
		inhoud = inhoud.encode("utf-8")
	if len(inhoud) > MAX_BESTAND:
		frappe.throw(_("Het bestand is te groot."))
	try:
		wortel = ET.fromstring(inhoud)
	except Exception:
		frappe.throw(_("Het bestand is geen geldige XML."))
	for el in wortel.iter():
		if isinstance(el.tag, str) and "}" in el.tag:
			el.tag = el.tag.split("}", 1)[1]
	return wortel


def _tekst(el, pad: str) -> str:
	gevonden = el.find(pad) if el is not None else None
	return (gevonden.text or "").strip() if gevonden is not None else ""


def lees(inhoud: bytes | str) -> list[dict]:
	"""De afschriften uit een CAMT.053-bestand: `[{iban, valuta, afschrift, regels: [...]}]`.

	Een regel: datum, bedrag (altijd positief), `bij` (True = ontvangen), naam en IBAN van de tegenpartij, omschrijving,
	kenmerk (EndToEndId) en `id` (het kenmerk van de bank, uniek per regel)."""
	wortel = ontleed(inhoud)
	afschriften = wortel.findall("BkToCstmrStmt/Stmt")
	if not afschriften:
		frappe.throw(_("Dit is geen bankafschrift in CAMT.053."))
	uit = []
	for stmt in afschriften:
		iban = schoon_iban(_tekst(stmt, "Acct/Id/IBAN") or _tekst(stmt, "Acct/Id/Othr/Id"))
		regels = []
		for nr, ntry in enumerate(stmt.findall("Ntry"), start=1):
			regels += _regels(ntry, iban, _tekst(stmt, "Id"), nr)
		uit.append({"iban": iban, "valuta": _tekst(stmt, "Acct/Ccy"), "afschrift": _tekst(stmt, "Id"), "regels": regels})
	return uit


def _regels(ntry, iban: str, afschrift: str, nr: int) -> list[dict]:
	bedrag_el = ntry.find("Amt")
	bedrag = flt(bedrag_el.text if bedrag_el is not None else 0, 2)
	bij = _tekst(ntry, "CdtDbtInd") != "DBIT"
	datum = _tekst(ntry, "BookgDt/Dt") or _tekst(ntry, "BookgDt/DtTm")[:10] or _tekst(ntry, "ValDt/Dt")
	basis = {
		"datum": str(getdate(datum)) if datum else None,
		"bij": bij,
		"valuta": (bedrag_el.get("Ccy") if bedrag_el is not None else "") or "",
		"soort": _tekst(ntry, "BkTxCd/Prtry/Cd") or _tekst(ntry, "BkTxCd/Domn/Fmly/SubFmlyCd"),
	}
	bank_id = _tekst(ntry, "AcctSvcrRef")
	details = ntry.findall("NtryDtls/TxDtls")
	delen = [flt(_tekst(d, "Amt") or _tekst(d, "AmtDtls/TxAmt/Amt"), 2) for d in details]
	# Een verzamelpost splitsen we alleen als de delen samen het bedrag van de regel zijn; anders blijft het één regel.
	los = len(details) > 1 and all(delen) and abs(sum(delen) - bedrag) < 0.005
	regels = []
	for i, detail in enumerate(details if los else details[:1] or [None]):
		wie = "Dbtr" if bij else "Cdtr"
		naam = _tekst(detail, f"RltdPties/{wie}/Nm") or _tekst(detail, f"RltdPties/{wie}/Pty/Nm")
		tegen = _tekst(detail, f"RltdPties/{wie}Acct/Id/IBAN") or _tekst(detail, f"RltdPties/{wie}Acct/Id/Othr/Id")
		vrij = [u.text.strip() for u in (detail.findall("RmtInf/Ustrd") if detail is not None else []) if u.text]
		vast = _tekst(detail, "RmtInf/Strd/CdtrRefInf/Ref")
		kenmerk = _tekst(detail, "Refs/EndToEndId")
		if kenmerk.upper() == "NOTPROVIDED":
			kenmerk = ""
		omschrijving = " ".join([*vrij, vast]).strip() or _tekst(ntry, "AddtlNtryInf")
		regel = {
			**basis,
			"bedrag": delen[i] if los else bedrag,
			"naam": naam,
			"tegenrekening": schoon_iban(tegen),
			"omschrijving": omschrijving,
			"kenmerk": kenmerk,
		}
		eigen = (_tekst(detail, "Refs/AcctSvcrRef") if los else "") or (f"{bank_id}-{i + 1}" if los and bank_id else bank_id)
		if not eigen:
			# Geen kenmerk van de bank: dan de inhoud van de regel zelf, met de plek in het afschrift erbij.
			bron = "|".join(str(x) for x in (iban, afschrift, nr, i, regel["datum"], regel["bedrag"], bij, omschrijving))
			eigen = "h" + hashlib.sha256(bron.encode()).hexdigest()[:30]
		regel["id"] = eigen[:140]
		regels.append(regel)
	return regels


def bankrekening_van(iban: str) -> frappe._dict | None:
	"""De eigen bankrekening (Bank Account) met dit IBAN."""
	for r in frappe.get_all(
		"Bank Account",
		filters={"is_company_account": 1, "disabled": 0, "iban": ("is", "set")},
		fields=["name", "iban", "company", "account"],
	):
		if schoon_iban(r.iban) == iban:
			return r
	return None


def inlezen(inhoud: bytes | str, afletteren: bool = True) -> dict:
	"""Maakt banktransacties van een CAMT.053-bestand en lettert af waar het zeker is.
	Geeft `{nieuw, dubbel, afgeletterd, open, rekeningen}`."""
	afschriften = lees(inhoud)
	uit = {"nieuw": 0, "dubbel": 0, "afgeletterd": 0, "open": 0, "rekeningen": []}
	for afschrift in afschriften:
		rekening = bankrekening_van(afschrift["iban"])
		if not rekening:
			frappe.throw(_("Er is geen eigen bankrekening met IBAN {0}. Maak die eerst aan (Bankrekening).").format(afschrift["iban"] or "?"))
		if not rekening.account:
			frappe.throw(_("Bankrekening {0} heeft nog geen grootboekrekening.").format(rekening.name))
		if rekening.name not in uit["rekeningen"]:
			uit["rekeningen"].append(rekening.name)
		for regel in afschrift["regels"]:
			if not regel["bedrag"] or not regel["datum"]:
				continue
			if frappe.db.exists("Bank Transaction", {"bank_account": rekening.name, "transaction_id": regel["id"], "docstatus": ("<", 2)}):
				uit["dubbel"] += 1
				continue
			transactie = frappe.get_doc(
				{
					"doctype": "Bank Transaction",
					"date": regel["datum"],
					"bank_account": rekening.name,
					"company": rekening.company,
					"currency": regel["valuta"] or afschrift["valuta"] or "EUR",
					"deposit": regel["bedrag"] if regel["bij"] else 0,
					"withdrawal": 0 if regel["bij"] else regel["bedrag"],
					"description": regel["omschrijving"][:1000] or regel["naam"],
					"reference_number": regel["kenmerk"],
					"transaction_id": regel["id"],
					"transaction_type": regel["soort"][:140],
					"bank_party_name": regel["naam"][:140],
					"bank_party_iban": regel["tegenrekening"][:140],
				}
			)
			transactie.insert()
			transactie.submit()
			uit["nieuw"] += 1
			if afletteren and letter_af(transactie.name):
				uit["afgeletterd"] += 1
			else:
				uit["open"] += 1
	return uit


def _kaal(tekst: str | None) -> str:
	return re.sub(r"[^A-Z0-9]", "", str(tekst or "").upper())


def voorstel(transactie: str) -> list[dict]:
	"""De facturen waar deze banktransactie zeker bij hoort: `[{doctype, naam, bedrag}]`, of leeg als het niet zeker is.

	Zeker = het factuurnummer (bij inkoop ook het nummer van de leverancier) staat in de omschrijving of het kenmerk, en
	het bedrag van de transactie is precies wat openstaat. Bij één factuur met een G-bedrag telt ook een van de twee
	delen. Meer facturen in één betaling mag, als ze samen precies het bedrag zijn."""
	t = frappe.db.get_value(
		"Bank Transaction",
		transactie,
		["company", "deposit", "withdrawal", "unallocated_amount", "description", "reference_number", "bank_party_iban"],
		as_dict=True,
	)
	if not t or flt(t.unallocated_amount) <= 0:
		return []
	bij = flt(t.deposit) > 0
	doctype = "Sales Invoice" if bij else "Purchase Invoice"
	velden = ["name", "outstanding_amount", "grand_total"]
	if not bij:
		velden.append("bill_no")
	if frappe.db.has_column(doctype, "g_bedrag"):
		velden.append("g_bedrag")
	tekst = _kaal(f"{t.description} {t.reference_number}")
	gevonden = []
	for f in frappe.get_all(doctype, filters={"company": t.company, "docstatus": 1, "outstanding_amount": (">", 0)}, fields=velden):
		nummers = [_kaal(f.name), _kaal(f.get("bill_no"))]
		# Een kort leveranciersnummer ("12") staat al snel toevallig in een omschrijving: pas vanaf vijf tekens.
		if any(n and len(n) >= 5 and n in tekst for n in nummers):
			gevonden.append(f)
	bedrag = flt(t.unallocated_amount, 2)
	if not gevonden:
		return []
	if abs(sum(flt(f.outstanding_amount) for f in gevonden) - bedrag) < 0.005:
		return [{"doctype": doctype, "naam": f.name, "bedrag": flt(f.outstanding_amount, 2)} for f in gevonden]
	if len(gevonden) == 1:
		f = gevonden[0]
		g = flt(f.get("g_bedrag"), 2)
		if g and (abs(bedrag - g) < 0.005 or abs(bedrag - (flt(f.grand_total) - g)) < 0.005) and bedrag <= flt(f.outstanding_amount) + 0.005:
			return [{"doctype": doctype, "naam": f.name, "bedrag": bedrag}]
	return []


def letter_af(transactie: str) -> bool:
	"""Boekt de betaling van de facturen uit `voorstel` en koppelt die aan de banktransactie. False = niets gedaan."""
	from erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool import _reconcile_vouchers
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	facturen = voorstel(transactie)
	if not facturen:
		return False
	t = frappe.db.get_value("Bank Transaction", transactie, ["bank_account", "date", "reference_number", "name"], as_dict=True)
	grootboek = frappe.db.get_value("Bank Account", t.bank_account, "account")
	bonnen = []
	frappe.db.savepoint("openaec_afletteren")
	try:
		for f in facturen:
			betaling = get_payment_entry(f["doctype"], f["naam"], party_amount=f["bedrag"], bank_account=grootboek)
			betaling.posting_date = t.date
			betaling.reference_no = (t.reference_number or t.name)[:140]
			betaling.reference_date = t.date
			betaling.bank_account = t.bank_account
			betaling.insert()
			betaling.submit()
			bonnen.append({"payment_doctype": "Payment Entry", "payment_name": betaling.name, "amount": f["bedrag"]})
		_reconcile_vouchers(transactie, bonnen, is_new_voucher=True)
	except Exception:
		# Een factuur die niet te betalen valt (gesloten periode, geblokkeerd) houdt het inlezen niet tegen.
		frappe.db.rollback(save_point="openaec_afletteren")
		frappe.log_error(title=f"OpenAEC Bouw: afletteren van {transactie} mislukt")
		return False
	return True


def _mag_bank() -> None:
	frappe.only_for(["Accounts Manager", "Accounts User", "System Manager"])


def bestand(file_url: str) -> bytes:
	"""De inhoud van een geüpload bestand waar deze gebruiker bij mag."""
	naam = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not naam:
		frappe.throw(_("Het bestand is niet gevonden."))
	doc = frappe.get_doc("File", naam)
	doc.check_permission("read")
	return doc.get_content()


@frappe.whitelist(methods=["POST"])
def inlezen_bestand(file_url: str) -> dict:
	"""Voor de knop op de lijst met banktransacties: leest een geüpload CAMT.053-bestand in."""
	_mag_bank()
	frappe.has_permission("Bank Transaction", "create", throw=True)
	inhoud = bestand(file_url)
	if isinstance(inhoud, str):
		inhoud = inhoud.encode("utf-8")
	return inlezen(inhoud)


@frappe.whitelist(methods=["POST"])
def letter_open_af(bankrekening: str | None = None) -> dict:
	"""Probeert de nog open banktransacties opnieuw af te letteren (bijvoorbeeld nadat facturen zijn geboekt)."""
	_mag_bank()
	filters = {"docstatus": 1, "unallocated_amount": (">", 0)}
	if bankrekening:
		filters["bank_account"] = bankrekening
	gelukt = 0
	namen = frappe.get_all("Bank Transaction", filters=filters, pluck="name", limit=500)
	for naam in namen:
		if frappe.has_permission("Bank Transaction", "write", doc=naam) and letter_af(naam):
			gelukt += 1
	return {"bekeken": len(namen), "afgeletterd": gelukt}
