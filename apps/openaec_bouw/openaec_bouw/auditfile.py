"""Auditfile Financieel (XAF 3.2): de administratie van een boekjaar als het bestand dat accountants en de
Belastingdienst inlezen.

Inhoud: het bedrijf, de relaties, het grootboek (met de RGS-code als `leadCode`), de btw-codes, de perioden, de
beginbalans en alle grootboekmutaties per dagboek. De bron is `GL Entry`; geannuleerde boekingen tellen niet mee.

Het bestand volgt de opbouw van XAF 3.2, maar is nog niet tegen het officiële XSD gevalideerd en niet in een
accountantspakket ingelezen. Zie `tests/test_boekhouding.py` voor wat wel bewaakt wordt (sluitende totalen).
"""

from xml.etree import ElementTree as ET

import frappe
from frappe import _
from frappe.utils import add_days, flt, formatdate, get_last_day, getdate, now_datetime

from openaec_bouw import __version__
from openaec_bouw.boekhouding import BTW_CODES, BTW_TEKSTEN

NS = "http://www.auditfiles.nl/XAF/3.2"
BALANS = ("Asset", "Liability", "Equity")


def _el(ouder, naam: str, tekst=None):
	el = ET.SubElement(ouder, naam)
	if tekst is not None:
		el.text = str(tekst)
	return el


def _bedrag(waarde) -> str:
	return f"{flt(waarde, 2):.2f}"


def _acc_id(rekening: frappe._dict) -> str:
	return (rekening.account_number or rekening.name)[:35]


def maak(bedrijf: str, boekjaar: str) -> bytes:
	"""De auditfile van `bedrijf` over `boekjaar` als XML (UTF-8)."""
	jaar = frappe.db.get_value("Fiscal Year", boekjaar, ["year_start_date", "year_end_date"], as_dict=True)
	if not jaar:
		frappe.throw(_("Onbekend boekjaar {0}").format(boekjaar))
	firma = frappe.db.get_value("Company", bedrijf, ["name", "company_name", "tax_id", "default_currency", "country"], as_dict=True)
	if not firma:
		frappe.throw(_("Onbekend bedrijf {0}").format(bedrijf))
	van, tot = getdate(jaar.year_start_date), getdate(jaar.year_end_date)

	velden = ["name", "account_name", "account_number", "root_type", "is_group"]
	if frappe.db.has_column("Account", "rgs_code"):
		velden.append("rgs_code")
	rekeningen = {r.name: r for r in frappe.get_all("Account", filters={"company": bedrijf, "is_group": 0}, fields=velden)}

	boekingen = frappe.get_all(
		"GL Entry",
		filters={"company": bedrijf, "is_cancelled": 0, "posting_date": ("between", [van, tot]), "is_opening": "No"},
		fields=["name", "posting_date", "account", "debit", "credit", "voucher_type", "voucher_no", "remarks", "party_type", "party"],
		order_by="posting_date asc, voucher_type asc, voucher_no asc, creation asc",
	)
	# Beginbalans: het saldo van de balansrekeningen vóór het boekjaar, plus wat in het jaar als opening is geboekt.
	openingen = frappe.db.sql(
		"""select account, sum(debit) - sum(credit) as saldo from `tabGL Entry`
		where company = %(bedrijf)s and is_cancelled = 0
		and (posting_date < %(van)s or (is_opening = 'Yes' and posting_date between %(van)s and %(tot)s))
		group by account having abs(sum(debit) - sum(credit)) >= 0.005""",
		{"bedrijf": bedrijf, "van": van, "tot": tot},
		as_dict=True,
	)
	openingen = [o for o in openingen if rekeningen.get(o.account) and rekeningen[o.account].root_type in BALANS]

	wortel = ET.Element("auditfile", {"xmlns": NS})
	kop = _el(wortel, "header")
	_el(kop, "fiscalYear", van.year)
	_el(kop, "startDate", van.isoformat())
	_el(kop, "endDate", tot.isoformat())
	_el(kop, "curCode", firma.default_currency or "EUR")
	_el(kop, "dateCreated", now_datetime().date().isoformat())
	_el(kop, "softwareDesc", "OpenAEC Bouw op ERPNext")
	_el(kop, "softwareVersion", __version__)

	co = _el(wortel, "company")
	_el(co, "companyIdent", firma.name[:35])
	_el(co, "companyName", firma.company_name or firma.name)
	_el(co, "taxRegistrationCountry", "NL")
	_el(co, "taxRegIdent", (firma.tax_id or "").replace(" ", "")[:30])

	# Relaties die in dit jaar in het grootboek voorkomen.
	partijen = sorted({(b.party_type, b.party) for b in boekingen if b.party and b.party_type in ("Customer", "Supplier")})
	if partijen:
		relaties = _el(co, "customersSuppliers")
		for soort, naam in partijen:
			veld = "customer_name" if soort == "Customer" else "supplier_name"
			gegevens = frappe.db.get_value(soort, naam, [veld, "tax_id"], as_dict=True) or frappe._dict()
			relatie = _el(relaties, "customerSupplier")
			_el(relatie, "custSupID", naam[:35])
			_el(relatie, "custSupName", gegevens.get(veld) or naam)
			if gegevens.get("tax_id"):
				_el(relatie, "taxRegIdent", gegevens.tax_id.replace(" ", "")[:30])
			_el(relatie, "custSupTp", "C" if soort == "Customer" else "S")

	grootboek = _el(co, "generalLedger")
	for r in sorted(rekeningen.values(), key=_acc_id):
		rekening = _el(grootboek, "ledgerAccount")
		_el(rekening, "accID", _acc_id(r))
		_el(rekening, "accDesc", r.account_name)
		_el(rekening, "accTp", "B" if r.root_type in BALANS else "P")
		if r.get("rgs_code"):
			_el(rekening, "leadCode", r.rgs_code)
			_el(rekening, "leadReference", "RGS")

	btw = _el(co, "vatCodes")
	for code in BTW_CODES:
		regel = _el(btw, "vatCode")
		_el(regel, "vatID", code)
		_el(regel, "vatDesc", BTW_TEKSTEN[code])

	perioden = _el(co, "periods")
	begin, nummer, periode_van = van, 0, {}
	while begin <= tot:
		nummer += 1
		eind = min(getdate(get_last_day(begin)), tot)
		periode = _el(perioden, "period")
		_el(periode, "periodNumber", nummer)
		_el(periode, "periodDesc", formatdate(begin, "MMMM yyyy"))
		_el(periode, "startDatePeriod", begin.isoformat())
		_el(periode, "endDatePeriod", eind.isoformat())
		periode_van[(begin.year, begin.month)] = nummer
		begin = getdate(add_days(eind, 1))

	if openingen:
		balans = _el(co, "openingBalance")
		_el(balans, "opBalDate", van.isoformat())
		_el(balans, "opBalDesc", "Beginbalans")
		_el(balans, "linesCount", len(openingen))
		_el(balans, "totalDebit", _bedrag(sum(o.saldo for o in openingen if o.saldo > 0)))
		_el(balans, "totalCredit", _bedrag(sum(-o.saldo for o in openingen if o.saldo < 0)))
		for nr, o in enumerate(sorted(openingen, key=lambda o: _acc_id(rekeningen[o.account])), start=1):
			lijn = _el(balans, "obLine")
			_el(lijn, "nr", nr)
			_el(lijn, "accID", _acc_id(rekeningen[o.account]))
			_el(lijn, "amnt", _bedrag(abs(o.saldo)))
			_el(lijn, "amntTp", "D" if o.saldo > 0 else "C")

	mutaties = _el(co, "transactions")
	_el(mutaties, "linesCount", len(boekingen))
	_el(mutaties, "totalDebit", _bedrag(sum(flt(b.debit) for b in boekingen)))
	_el(mutaties, "totalCredit", _bedrag(sum(flt(b.credit) for b in boekingen)))
	dagboeken, posten = {}, {}
	for b in boekingen:
		posten.setdefault((b.voucher_type, b.voucher_no), []).append(b)
	for (soort, bon), regels in posten.items():
		if soort not in dagboeken:
			dagboek = _el(mutaties, "journal")
			_el(dagboek, "jrnID", soort[:35])
			_el(dagboek, "desc", _(soort))
			_el(dagboek, "jrnTp", {"Sales Invoice": "S", "Purchase Invoice": "P", "Payment Entry": "B"}.get(soort, "M"))
			dagboeken[soort] = dagboek
		datum = getdate(regels[0].posting_date)
		post = _el(dagboeken[soort], "transaction")
		_el(post, "nr", bon[:35])
		_el(post, "desc", (regels[0].remarks or bon)[:9999])
		_el(post, "periodNumber", periode_van.get((datum.year, datum.month), 1))
		_el(post, "trDt", datum.isoformat())
		_el(post, "amnt", _bedrag(sum(flt(r.debit) for r in regels)))
		for nr, r in enumerate(regels, start=1):
			rekening = rekeningen.get(r.account) or frappe._dict(name=r.account, account_number=None)
			lijn = _el(post, "trLine")
			_el(lijn, "nr", nr)
			_el(lijn, "accID", _acc_id(rekening))
			_el(lijn, "docRef", bon[:255])
			_el(lijn, "effDate", getdate(r.posting_date).isoformat())
			_el(lijn, "desc", (r.remarks or bon)[:9999])
			_el(lijn, "amnt", _bedrag(flt(r.debit) or flt(r.credit)))
			_el(lijn, "amntTp", "D" if flt(r.debit) else "C")
			if r.party and r.party_type in ("Customer", "Supplier"):
				_el(lijn, "custSupID", r.party[:35])

	ET.indent(wortel, space=" ")
	return ET.tostring(wortel, encoding="utf-8", xml_declaration=True)


@frappe.whitelist()
def download(bedrijf: str, boekjaar: str):
	"""Stuurt de auditfile als download. Alleen voor wie de boekhouding mag inzien."""
	frappe.only_for(["Accounts Manager", "Auditor", "System Manager"])
	frappe.has_permission("Company", "read", bedrijf, throw=True)
	inhoud = maak(bedrijf, boekjaar)
	afkorting = frappe.db.get_value("Company", bedrijf, "abbr") or "bedrijf"
	frappe.response.filename = f"auditfile-{frappe.scrub(afkorting)}-{frappe.scrub(boekjaar)}.xaf"
	frappe.response.filecontent = inhoud
	frappe.response.type = "download"
	frappe.response.content_type = "application/xml"
