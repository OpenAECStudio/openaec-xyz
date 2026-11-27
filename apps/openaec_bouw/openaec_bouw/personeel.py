"""Personeel: contract, cao, verlof in uren en feestdagen per bedrijf. Ontwerp: `docs/personeel-cao-verlof.md`.

Frappe HR doet het aanvragen en goedkeuren van verlof; het saldo staat hier, in uren, als verlofboekingen. Voor een
verlofsoort in uren (vinkje `in_uren` op de verlofsoort) slaat de verlofaanvraag de controles in dagen van Frappe over
(`verlofaanvraag.py`); de controle in uren gebeurt hier.

- Welk contract en welke cao-periode gelden, volgt altijd uit de datum. Wisselt er iets midden in een maand, dan
  wordt die maand in stukken gerekend.
- Opbouw achteraf, op de laatste dag van de maand: jaaruren × contractfactor / 12, naar rato van de dagen.
- Verval per opbouwjaar, oudste eerst.
"""

import calendar
from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, add_months, cint, flt, get_last_day, getdate, today

WEEKDAGEN = ("Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag")
ZONDER_ROOSTER = ("Nulurencontract", "Oproepcontract")

# Naam in de bibliotheek `holidays` (Nederlands) → feestdag in de cao.
FEESTDAG_NAMEN = {
	"Nieuwjaarsdag": "Nieuwjaarsdag",
	"Goede vrijdag": "Goede Vrijdag",
	"Eerste paasdag": "Eerste Paasdag",
	"Tweede paasdag": "Tweede Paasdag",
	"Koningsdag": "Koningsdag",
	"Koninginnedag": "Koningsdag",
	"Bevrijdingsdag": "Bevrijdingsdag",
	"Hemelvaartsdag": "Hemelvaartsdag",
	"Eerste pinksterdag": "Eerste Pinksterdag",
	"Tweede pinksterdag": "Tweede Pinksterdag",
	"Eerste kerstdag": "Eerste Kerstdag",
	"Tweede kerstdag": "Tweede Kerstdag",
}


# --- Wat geldt op een datum -------------------------------------------------------------------------------------


def contract_op(medewerker: str, datum) -> frappe._dict | None:
	datum = getdate(datum)
	rijen = frappe.get_all(
		"Arbeidscontract",
		filters={"medewerker": medewerker, "van": ("<=", datum)},
		or_filters=[["tot", "is", "not set"], ["tot", ">=", datum]],
		fields=["name"],
		order_by="van desc",
		limit=1,
	)
	return frappe.get_cached_doc("Arbeidscontract", rijen[0].name) if rijen else None


def periode_op(cao: str, groep: str, datum) -> str | None:
	"""De cao-periode die op een datum geldt; een periode zonder einddatum loopt door."""
	if not cao:
		return None
	datum = getdate(datum)
	rijen = frappe.get_all(
		"Cao Periode",
		filters={"cao": cao, "werknemersgroep": groep, "geldig_van": ("<=", datum)},
		or_filters=[["geldig_tot", "is", "not set"], ["geldig_tot", ">=", datum]],
		pluck="name",
		order_by="geldig_van desc",
		limit=1,
	)
	return rijen[0] if rijen else None


def volgende_periode(cao: str, groep: str, datum) -> str | None:
	rijen = frappe.get_all(
		"Cao Periode",
		filters={"cao": cao, "werknemersgroep": groep, "geldig_van": (">", getdate(datum))},
		pluck="name",
		order_by="geldig_van asc",
		limit=1,
	)
	return rijen[0] if rijen else None


def contractfactor(contract, periode: str | None) -> float:
	if contract.soort in ZONDER_ROOSTER:
		return 0.0
	norm = flt(frappe.db.get_value("Cao Periode", periode, "normuren_per_week")) if periode else 0
	return flt(contract.uren_per_week) / (norm or 40)


def uren_op_dag(contract, datum) -> float:
	"""Hoeveel uur iemand volgens zijn werkpatroon op een dag zou werken. Week A is de week van de ingangsdatum."""
	datum = getdate(datum)
	dag = WEEKDAGEN[datum.weekday()]
	weken = ((datum - timedelta(days=datum.weekday())) - (getdate(contract.van) - timedelta(days=getdate(contract.van).weekday()))).days // 7
	week = "A" if weken % 2 == 0 else "B"
	uren = 0.0
	for rij in contract.werkpatroon:
		if rij.weekdag == dag and (rij.week or "") in ("", week):
			uren += flt(rij.uren)
	return uren


# --- Feestdagen -------------------------------------------------------------------------------------------------


def feestdagen_nl(jaar: int) -> dict:
	"""Datum → feestdag (naam uit de cao) voor een jaar; Bevrijdingsdag staat er elk jaar in."""
	import holidays

	dagen = {}
	for datum, naam in holidays.country_holidays("NL", years=jaar, language="nl").items():
		if naam in FEESTDAG_NAMEN:
			dagen[datum] = FEESTDAG_NAMEN[naam]
	dagen[date(jaar, 5, 5)] = "Bevrijdingsdag"
	return dagen


def vrije_dagen(periode: str, jaar: int) -> list[dict]:
	"""De vrije dagen van een jaar volgens één cao-periode: feestdagen die vrij zijn, en de collectieve dagen."""
	p = frappe.get_cached_doc("Cao Periode", periode)
	regels = {r.feestdag: r for r in p.feestdagen}
	dagen = []
	for datum, naam in sorted(feestdagen_nl(jaar).items()):
		regel = regels.get(naam)
		if not regel or not regel.vrij:
			continue
		if naam == "Bevrijdingsdag" and regel.eens_per_vijf_jaar and jaar % 5:
			continue
		dagen.append({"datum": datum, "omschrijving": naam, "soort": "Feestdag"})
	for rij in p.collectieve_dagen:
		if getdate(rij.datum).year == jaar:
			dagen.append({"datum": getdate(rij.datum), "omschrijving": rij.omschrijving or _("Collectief vrij"), "soort": "Collectief", "verlofsoort": rij.verlofsoort})
	return dagen


def vrij_op(medewerker: str, datum) -> bool:
	"""Of een dag voor deze medewerker een vrije dag is volgens de feestdagenlijst die op dat moment geldt."""
	from erpnext.setup.doctype.employee.employee import is_holiday

	return bool(is_holiday(medewerker, getdate(datum), raise_exception=False, only_non_weekly=True))


# --- Saldo en boekingen -----------------------------------------------------------------------------------------


def in_uren(verlofsoort: str) -> bool:
	return bool(frappe.get_cached_value("Leave Type", verlofsoort, "in_uren"))


def saldo(medewerker: str, verlofsoort: str | None = None, datum=None) -> dict:
	"""Saldo in uren per verlofsoort op een datum (standaard vandaag)."""
	filters = {"medewerker": medewerker, "datum": ("<=", getdate(datum or today()))}
	if verlofsoort:
		filters["verlofsoort"] = verlofsoort
	uit = {}
	for r in frappe.get_all("Verlofboeking", filters=filters, fields=["verlofsoort", "uren"]):
		uit[r.verlofsoort] = uit.get(r.verlofsoort, 0) + r.uren
	return {k: flt(v, 2) for k, v in uit.items()}


def boek(medewerker, verlofsoort, soort, datum, uren, **extra):
	doc = frappe.get_doc({
		"doctype": "Verlofboeking", "medewerker": medewerker, "verlofsoort": verlofsoort, "soort": soort,
		"datum": getdate(datum), "uren": flt(uren, 2), **extra,
	})
	doc.flags.door_systeem = True
	doc.insert(ignore_permissions=True)
	return doc


# --- Opbouw -----------------------------------------------------------------------------------------------------


def _stukken(medewerker: str, begin: date, eind: date):
	"""Deelt een periode op in stukken met hetzelfde contract en dezelfde cao-periode."""
	stukken, dag = [], begin
	while dag <= eind:
		contract = contract_op(medewerker, dag)
		periode = periode_op(contract.cao, contract.werknemersgroep, dag) if contract else None
		sleutel = (contract.name if contract else None, periode)
		if stukken and stukken[-1]["sleutel"] == sleutel:
			stukken[-1]["tot"] = dag
		else:
			stukken.append({"sleutel": sleutel, "contract": contract, "periode": periode, "van": dag, "tot": dag})
		dag += timedelta(days=1)
	return [s for s in stukken if s["contract"] and s["periode"]]


def opbouw_maand(jaar: int, maand: int, medewerker: str | None = None) -> int:
	"""Boekt de opbouw van een maand, op de laatste dag. Opnieuw draaien vervangt de opbouw van die maand."""
	begin, eind = date(jaar, maand, 1), date(jaar, maand, calendar.monthrange(jaar, maand)[1])
	dagen_in_maand = (eind - begin).days + 1
	medewerkers = [medewerker] if medewerker else frappe.get_all(
		"Arbeidscontract", filters={"van": ("<=", eind)}, or_filters=[["tot", "is", "not set"], ["tot", ">=", begin]],
		pluck="medewerker", distinct=True,
	)
	aantal = 0
	for mw in medewerkers:
		frappe.db.delete("Verlofboeking", {"medewerker": mw, "soort": "Opbouw", "datum": eind})
		totaal = {}
		for stuk in _stukken(mw, begin, eind):
			contract, periode = stuk["contract"], frappe.get_cached_doc("Cao Periode", stuk["periode"])
			deel = ((stuk["tot"] - stuk["van"]).days + 1) / dagen_in_maand
			factor = contractfactor(contract, periode.name)
			gewerkt = _gewerkte_uren(mw, stuk["van"], stuk["tot"]) if contract.soort in ZONDER_ROOSTER else 0
			for recht in periode.verlofrechten:
				if contract.soort in ZONDER_ROOSTER:
					uren = gewerkt * flt(recht.per_gewerkt_uur) / 100
				else:
					uren = flt(recht.uren_per_jaar) * factor / 12 * deel
				sleutel = (recht.verlofsoort, contract.name, periode.name)
				totaal[sleutel] = totaal.get(sleutel, 0) + uren
		for (verlofsoort, contract, periode), uren in totaal.items():
			if flt(uren, 2):
				boek(mw, verlofsoort, "Opbouw", eind, uren, opbouwjaar=jaar, contract=contract, cao_periode=periode)
				aantal += 1
	return aantal


def _gewerkte_uren(medewerker: str, van: date, tot: date) -> float:
	"""Goedgekeurde uren uit de urenstaten, voor opbouw per gewerkt uur."""
	rij = frappe.db.sql(
		"""select sum(d.hours) from `tabTimesheet Detail` d join `tabTimesheet` t on t.name = d.parent
		where t.employee = %s and t.docstatus = 1 and date(d.from_time) between %s and %s""",
		(medewerker, van, tot),
	)
	return flt(rij[0][0]) if rij else 0.0


# --- Verval -----------------------------------------------------------------------------------------------------


def vervaldatum(regel: str, opbouwjaar: int) -> date | None:
	if regel == "Zes maanden na het jaar":
		return date(opbouwjaar + 1, 7, 1)
	if regel == "Vijf jaar na het jaar":
		return date(opbouwjaar + 6, 1, 1)
	if regel == "Einde van het jaar":
		return date(opbouwjaar + 1, 1, 1)
	return None


def _verval_regel(verlofsoort: str, cao_periode: str | None) -> str:
	if cao_periode:
		for recht in frappe.get_cached_doc("Cao Periode", cao_periode).verlofrechten:
			if recht.verlofsoort == verlofsoort:
				return recht.verval
	return "Nooit"


def per_opbouwjaar(medewerker: str, verlofsoort: str, datum=None) -> dict:
	"""Wat er per opbouwjaar nog over is: opname en uitbetaling gaan eerst van het oudste jaar af."""
	rijen = frappe.get_all(
		"Verlofboeking",
		filters={"medewerker": medewerker, "verlofsoort": verlofsoort, "datum": ("<=", getdate(datum or today()))},
		fields=["soort", "uren", "opbouwjaar", "datum", "cao_periode"],
		order_by="datum asc, creation asc",
	)
	jaren, regels, af = {}, {}, 0.0
	for r in rijen:
		jaar = cint(r.opbouwjaar) or getdate(r.datum).year
		if r.uren > 0:
			jaren[jaar] = jaren.get(jaar, 0) + r.uren
			if r.cao_periode:
				regels[jaar] = r.cao_periode
		elif r.soort == "Verval":
			jaren[jaar] = jaren.get(jaar, 0) + r.uren
		else:
			af += -r.uren
	for jaar in sorted(jaren):
		gebruikt = min(max(jaren[jaar], 0), af)
		jaren[jaar] -= gebruikt
		af -= gebruikt
	return {"jaren": {j: flt(u, 2) for j, u in jaren.items()}, "regels": regels, "tekort": flt(af, 2)}


def verval(datum=None) -> int:
	"""Laat vervallen wat op `datum` over is van opbouwjaren waarvan de vervaldatum voorbij is."""
	datum = getdate(datum or today())
	aantal = 0
	for mw, soort in frappe.get_all("Verlofboeking", fields=["medewerker", "verlofsoort"], distinct=True, as_list=True):
		stand = per_opbouwjaar(mw, soort, datum)
		for jaar, rest in stand["jaren"].items():
			grens = vervaldatum(_verval_regel(soort, stand["regels"].get(jaar)), jaar)
			if grens and grens <= datum and rest > 0:
				boek(mw, soort, "Verval", grens, -rest, opbouwjaar=jaar)
				aantal += 1
	return aantal


# --- Verlofaanvraag in uren -------------------------------------------------------------------------------------


def uren_voor_aanvraag(medewerker: str, van, tot) -> float:
	"""Uren volgens het werkpatroon op de dagen van een aanvraag, zonder vrije dagen."""
	totaal, dag = 0.0, getdate(van)
	while dag <= getdate(tot):
		contract = contract_op(medewerker, dag)
		if contract and not vrij_op(medewerker, dag):
			totaal += uren_op_dag(contract, dag)
		dag += timedelta(days=1)
	return flt(totaal, 2)


def aanvraag_controleren(doc, method=None):
	"""Verlofaanvraag: uren voorstellen uit het werkpatroon en het saldo in uren toetsen."""
	if not doc.leave_type or not in_uren(doc.leave_type) or not doc.from_date or not doc.to_date:
		return
	voorstel = uren_voor_aanvraag(doc.employee, doc.from_date, doc.to_date)
	if not flt(doc.uren) or doc.has_value_changed("from_date") or doc.has_value_changed("to_date"):
		doc.uren = voorstel / 2 if doc.half_day and doc.from_date == doc.to_date else voorstel
	if flt(doc.uren) <= 0:
		frappe.throw(_("Op deze dagen staan geen werkuren in het rooster: hier is geen verlof voor nodig."))
	if frappe.get_cached_value("Leave Type", doc.leave_type, "negatief_in_uren"):
		return
	beschikbaar = saldo(doc.employee, doc.leave_type, doc.to_date).get(doc.leave_type, 0)
	if doc.docstatus == 0 and doc.status != "Rejected" and flt(doc.uren) > beschikbaar + 0.005:
		frappe.throw(_("Te weinig saldo voor {0}: {1} uur nodig, {2} uur beschikbaar.").format(doc.leave_type, flt(doc.uren, 2), flt(beschikbaar, 2)))


def aanvraag_goedgekeurd(doc, method=None):
	if doc.status == "Approved" and in_uren(doc.leave_type):
		boek(doc.employee, doc.leave_type, "Opname", doc.from_date, -flt(doc.uren), bron_soort="Leave Application", bron=doc.name)


def aanvraag_geannuleerd(doc, method=None):
	frappe.db.delete("Verlofboeking", {"bron_soort": "Leave Application", "bron": doc.name})


# --- Bedrijfskalender -------------------------------------------------------------------------------------------


def maak_kalender(bedrijf: str, jaar: int, cao: str, groep: str):
	"""Maakt (of ververst, zolang hij concept is) de bedrijfskalender van een jaar uit de cao-periode van 1 januari."""
	naam = f"{bedrijf} {jaar} {cao} {groep}"
	if frappe.db.exists("Bedrijfskalender", naam):
		doc = frappe.get_doc("Bedrijfskalender", naam)
		if doc.status == "Vastgesteld":
			return doc
	else:
		doc = frappe.new_doc("Bedrijfskalender")
		doc.update({"bedrijf": bedrijf, "jaar": jaar, "cao": cao, "werknemersgroep": groep})
	periode = periode_op(cao, groep, date(jaar, 1, 1)) or volgende_periode(cao, groep, date(jaar - 1, 12, 31))
	eigen = [r.as_dict() for r in doc.dagen if r.soort == "Bedrijf"]
	doc.set("dagen", [])
	for dag in vrije_dagen(periode, jaar) if periode else []:
		doc.append("dagen", dag)
	for dag in eigen:
		doc.append("dagen", {k: dag[k] for k in ("datum", "omschrijving", "soort", "verlofsoort")})
	doc.save(ignore_permissions=True)
	return doc


def kalender_vaststellen(naam: str):
	"""Zet de kalender vast en maakt de feestdagenlijst van Frappe, gekoppeld aan de medewerkers met deze cao."""
	doc = frappe.get_doc("Bedrijfskalender", naam)
	lijst_naam = naam[:140]
	lijst = frappe.get_doc("Holiday List", lijst_naam) if frappe.db.exists("Holiday List", lijst_naam) else frappe.new_doc("Holiday List")
	lijst.update({"holiday_list_name": lijst_naam, "from_date": date(doc.jaar, 1, 1), "to_date": date(doc.jaar, 12, 31)})
	lijst.set("holidays", [{"holiday_date": d.datum, "description": d.omschrijving, "weekly_off": 0} for d in doc.dagen])
	lijst.save(ignore_permissions=True)
	doc.feestdagenlijst = lijst.name
	doc.status = "Vastgesteld"
	doc.save(ignore_permissions=True)
	for mw in _medewerkers_met_cao(doc.bedrijf, doc.cao, doc.werknemersgroep, doc.jaar):
		_toewijzen(mw, lijst.name, doc.jaar)
	return doc


def _toewijzen(medewerker: str, lijst: str, jaar: int):
	if frappe.db.exists("Holiday List Assignment", {"assigned_to": medewerker, "holiday_list": lijst, "docstatus": 1}):
		return
	toewijzing = frappe.get_doc({
		"doctype": "Holiday List Assignment", "applicable_for": "Employee", "assigned_to": medewerker,
		"holiday_list": lijst, "from_date": date(jaar, 1, 1),
	})
	toewijzing.insert(ignore_permissions=True)
	toewijzing.submit()


def kalenders_toewijzen(contract):
	"""Een nieuw of gewijzigd contract krijgt de vastgestelde kalenders van zijn cao voor de jaren die het loopt."""
	if not contract.cao:
		return
	eind = getdate(contract.tot).year if contract.tot else getdate(today()).year + 1
	for k in frappe.get_all(
		"Bedrijfskalender",
		filters={"bedrijf": contract.bedrijf, "cao": contract.cao, "werknemersgroep": contract.werknemersgroep, "status": "Vastgesteld",
			"jaar": ("between", (getdate(contract.van).year, eind)), "feestdagenlijst": ("is", "set")},
		fields=["feestdagenlijst", "jaar"],
	):
		_toewijzen(contract.medewerker, k.feestdagenlijst, k.jaar)


def _medewerkers_met_cao(bedrijf, cao, groep, jaar) -> list[str]:
	return frappe.get_all(
		"Arbeidscontract",
		filters={"bedrijf": bedrijf, "cao": cao, "werknemersgroep": groep, "van": ("<=", date(jaar, 12, 31))},
		or_filters=[["tot", "is", "not set"], ["tot", ">=", date(jaar, 1, 1)]],
		pluck="medewerker", distinct=True,
	)


# --- Elke dag ---------------------------------------------------------------------------------------------------


def dagelijks():
	"""Opbouw op de laatste dag van de maand, verval, status van contracten en cao-periodes, kalenders vooruit."""
	vandaag = getdate(today())
	if vandaag == getdate(get_last_day(vandaag)):
		opbouw_maand(vandaag.year, vandaag.month)
	verval(vandaag)
	contracten_bijwerken(vandaag)
	periodes_bijwerken(vandaag)
	if (vandaag.month, vandaag.day) == (10, 1):
		kalenders_vooruit(vandaag.year + 1)


def contracten_bijwerken(vandaag=None):
	vandaag = getdate(vandaag or today())
	for c in frappe.get_all("Arbeidscontract", fields=["name", "van", "tot", "status", "medewerker"]):
		status = "Toekomstig" if getdate(c.van) > vandaag else "Afgelopen" if c.tot and getdate(c.tot) < vandaag else "Lopend"
		if status != c.status:
			frappe.db.set_value("Arbeidscontract", c.name, "status", status, update_modified=False)
		if status == "Lopend":
			medewerker_bijwerken(c.medewerker, vandaag)


def medewerker_bijwerken(medewerker: str, vandaag=None):
	"""Zet het huidige contract en de cao op de medewerker, en de contractsoort van Frappe."""
	contract = contract_op(medewerker, vandaag or today())
	waarden = {"huidig_contract": contract.name if contract else None, "cao": contract.cao if contract else None}
	if contract:
		soort = {"Onbepaalde tijd": "Vast", "Bepaalde tijd": "Tijdelijk", "Inhuur": "Inhuur (zzp of uitzend)"}.get(contract.soort)
		if contract.soort in ("Nulurencontract", "Oproepcontract", "Min-maxcontract"):
			soort = "Oproep"
		elif contract.soort in ("Stage", "BBL"):
			soort = "Stage"
		if soort and frappe.db.exists("Employment Type", soort):
			waarden["employment_type"] = soort
		if contract.tot:
			waarden["contract_end_date"] = contract.tot
	frappe.db.set_value("Employee", medewerker, waarden, update_modified=False)


def periodes_bijwerken(vandaag=None):
	"""Verlopen periodes afsluiten, stilzwijgend verlengen, en melden als er over twee maanden niets meer geldt."""
	vandaag = getdate(vandaag or today())
	for p in frappe.get_all("Cao Periode", filters={"status": ("in", ("Vastgesteld", "Stilzwijgend verlengd")), "geldig_tot": ("is", "set")}, pluck="name"):
		doc = frappe.get_doc("Cao Periode", p)
		volgende = volgende_periode(doc.cao, doc.werknemersgroep, doc.geldig_tot)
		if getdate(doc.geldig_tot) < vandaag:
			if not volgende and doc.stilzwijgend_verlengen:
				verleng(doc)
			doc.db_set("status", "Verlopen")
		elif not volgende and getdate(doc.geldig_tot) <= add_months(vandaag, 2) and not doc.stilzwijgend_verlengen:
			_meld(doc, _("Cao {0} ({1}) loopt af op {2} en er is nog geen volgende periode.").format(doc.cao, doc.werknemersgroep, frappe.format(doc.geldig_tot, "Date")))


def verleng(doc):
	nieuw = frappe.copy_doc(doc)
	nieuw.geldig_van = add_days(doc.geldig_tot, 1)
	nieuw.geldig_tot = add_days(add_months(doc.geldig_tot, 12), 0)
	nieuw.status = "Stilzwijgend verlengd"
	nieuw.vorige_periode = doc.name
	nieuw.set("loonafspraken", [])
	nieuw.set("collectieve_dagen", [])
	nieuw.insert(ignore_permissions=True)
	return nieuw


def _meld(doc, tekst):
	vandaag = today()
	if frappe.db.exists("Comment", {"reference_doctype": doc.doctype, "reference_name": doc.name, "content": tekst, "creation": (">=", vandaag)}):
		return
	doc.add_comment("Comment", tekst)
	for gebruiker in frappe.get_all("Has Role", filters={"role": "HR Manager", "parenttype": "User"}, pluck="parent", distinct=True):
		frappe.get_doc({"doctype": "Notification Log", "for_user": gebruiker, "subject": tekst, "document_type": doc.doctype, "document_name": doc.name, "type": "Alert"}).insert(ignore_permissions=True)


def kalenders_vooruit(jaar: int):
	"""Maakt voor elke combinatie van bedrijf en cao de kalender van een jaar als concept."""
	combinaties = frappe.get_all("Arbeidscontract", filters={"cao": ("is", "set")}, fields=["bedrijf", "cao", "werknemersgroep"], distinct=True)
	for c in combinaties:
		maak_kalender(c.bedrijf, jaar, c.cao, c.werknemersgroep)


# --- Velden en stamgegevens ------------------------------------------------------------------------------------


VELDEN = {
	"Leave Type": [
		{"fieldname": "in_uren", "fieldtype": "Check", "label": "Saldo in uren (OpenAEC)", "insert_after": "leave_type_name",
			"description": "Het saldo staat in de verlofboekingen van OpenAEC, in uren; Frappe telt hier niet in dagen."},
		{"fieldname": "negatief_in_uren", "fieldtype": "Check", "label": "Negatief saldo in uren toegestaan", "insert_after": "in_uren", "depends_on": "in_uren"},
	],
	"Leave Application": [
		{"fieldname": "uren", "fieldtype": "Float", "label": "Uren", "insert_after": "total_leave_days", "precision": "2",
			"description": "Voorgesteld uit het werkpatroon, zonder vrije dagen. Aan te passen voor een deel van een dag."},
	],
	"Employee": [
		{"fieldname": "huidig_contract", "fieldtype": "Link", "options": "Arbeidscontract", "label": "Huidig contract", "insert_after": "employment_type", "read_only": 1},
		{"fieldname": "cao", "fieldtype": "Link", "options": "Cao", "label": "Cao", "insert_after": "huidig_contract", "read_only": 1},
		{"fieldname": "bsn", "fieldtype": "Data", "label": "BSN", "insert_after": "date_of_birth", "permlevel": 1},
	],
}

# Verlofsoorten van de module loon die in uren gaan; ziekte en onbetaald verlof blijven in dagen.
SOORTEN_IN_UREN = ("Vakantie (wettelijk)", "Vakantie (bovenwettelijk)", "Roostervrij (ATV)", "Bijzonder verlof")


def na_migratie():
	"""Velden op verlofsoort, verlofaanvraag en medewerker; de verlofsoorten van de module loon in uren; de cao's."""
	if "hrms" not in frappe.get_installed_apps():
		return
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(VELDEN, update=True)
	for soort in SOORTEN_IN_UREN:
		if frappe.db.exists("Leave Type", soort):
			frappe.db.set_value("Leave Type", soort, "in_uren", 1, update_modified=False)
	# Bijzonder verlof bouwt niet op: het wordt per gebeurtenis toegekend en mag dus onder nul.
	if frappe.db.exists("Leave Type", "Bijzonder verlof"):
		frappe.db.set_value("Leave Type", "Bijzonder verlof", "negatief_in_uren", 1, update_modified=False)
	_bsn_alleen_voor_hr()
	from openaec_bouw import cao_gegevens

	cao_gegevens.laden()


def _bsn_alleen_voor_hr():
	"""Het BSN staat op rechtenniveau 1 van de medewerker: alleen HR leest en schrijft het."""
	from frappe.permissions import add_permission, update_permission_property

	for rol in ("HR Manager", "HR User"):
		if not frappe.db.exists("Custom DocPerm", {"parent": "Employee", "role": rol, "permlevel": 1}):
			add_permission("Employee", rol, 1)
			update_permission_property("Employee", rol, 1, "write", 1)
