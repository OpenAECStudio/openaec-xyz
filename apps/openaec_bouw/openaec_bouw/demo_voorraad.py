"""Het demonstratiebedrijf, deel voorraad: de houthandel rekent met magazijnen, partijen en een grijpvoorraad.

Wat hier vooraf goed staat, omdat het na de eerste mutatie niet meer te veranderen is:

- de artikelen zijn **voorraadartikelen**, met eenheid, houtsoort, keurmerk en land van herkomst;
- de waardering is de **gemiddelde inkoopprijs**;
- tropisch hardhout loopt per **partij** (`Batch`) met het land en het gebied van herkomst, zodat een levering naar
  de kap te herleiden is;
- er zijn drie magazijnen: hoofdmagazijn, zagerij en **grijpvoorraad**. Uit de grijpvoorraad (schroeven, lijm,
  bouten) wordt zonder bon gepakt; het verbruik blijkt uit de telling per kwartaal.

De administratie wordt per maand gesimuleerd met de voorraad erbij: eerst inkoop (aan het begin van de maand), dan
verkoop, en nooit meer verkopen dan er ligt. Zo kan alles later in volgorde van datum geboekt worden zonder dat de
voorraad negatief wordt. Alles is concept.
"""

import datetime
import random

import frappe
from frappe.utils import flt

# (code, naam, groep, eenheid, kostprijs, opslag, soort, land, keurmerk, aandeel in de omzet)
ARTIKELEN = [
	("VUR-38140", "Vuren C24 geschaafd 38x140", "Naaldhout", "m", 2.35, 1.30, "eu", "Germany", "PEFC", 0.13),
	("VUR-45195", "Vuren C24 geschaafd 45x195", "Naaldhout", "m", 3.90, 1.30, "eu", "Germany", "PEFC", 0.10),
	("DGL-100200", "Douglas balk 100x200", "Naaldhout", "m", 14.20, 1.32, "eu", "Belgium", "PEFC", 0.08),
	("LAR-22195", "Lariks rabat 22x195", "Naaldhout", "m", 4.60, 1.35, "eu", "Belgium", "PEFC", 0.07),
	("EIK-K27", "Eiken kwartiers 27 mm", "Loofhout", "m³", 1380.0, 1.28, "eu", "Belgium", "FSC Mix", 0.05),
	("EIK-P20140", "Eiken planken geschaafd 20x140", "Loofhout", "m", 6.90, 1.40, "zagerij", "Belgium", "FSC Mix", 0.04),
	("AZO-D50200", "Azobé damwandplank 50x200", "Tropisch hardhout", "m", 15.80, 1.38, "tropisch", "Gabon", "FSC 100%", 0.14),
	("AZO-B150", "Azobé balk 150x150", "Tropisch hardhout", "m", 36.50, 1.38, "tropisch", "Gabon", "FSC 100%", 0.09),
	("MER-67114", "Meranti kozijnhout 67x114", "Tropisch hardhout", "m", 11.90, 1.36, "tropisch", "Brazil", "FSC Mix", 0.09),
	("BAN-28145", "Bankirai dekdeel 28x145", "Tropisch hardhout", "m", 7.40, 1.40, "tropisch", "Brazil", "FSC 100%", 0.08),
	("PAD-52", "Padoek gezaagd 52 mm", "Tropisch hardhout", "m³", 2150.0, 1.34, "tropisch", "Gabon", "FSC 100%", 0.04),
	("MPX-18", "Multiplex berken 18 mm 2500x1250", "Plaatmateriaal", "stuk", 58.0, 1.27, "nl", "Netherlands", "FSC Mix", 0.06),
	("OSB-18", "OSB3 18 mm 2440x1220", "Plaatmateriaal", "stuk", 19.5, 1.27, "nl", "Netherlands", "PEFC", 0.03),
]
# Grijpvoorraad: (code, naam, kostprijs per doos of koker, verbruik per kwartaal)
GRIJP = [
	("GRP-SPS570", "Spaanplaatschroeven 5x70 (doos 200)", 11.80, 140),
	("GRP-RVS560", "RVS vlonderschroeven 5x60 (doos 200)", 27.50, 90),
	("GRP-LIJM", "Houtlijm D3 (koker 750 g)", 8.40, 110),
	("GRP-BOUT", "Slotbouten M10x120 verzinkt (doos 50)", 24.90, 45),
]
# Bovenop de opslag per artikel: bezorgen, zaagloon en kleine orders. Samen ongeveer dertig procent brutomarge.
OPSLAG_EXTRA = 0.11
GEBIEDEN = {"Gabon": ["Concessie Ogooué-Ivindo", "Concessie Haut-Abanga"], "Brazil": ["Pará, Flona do Tapajós", "Mato Grosso, perceel Juruena"]}
SEIZOEN = [0.80, 0.85, 1.00, 1.10, 1.15, 1.15, 0.90, 0.85, 1.10, 1.10, 1.05, 0.95]
LEVERANCIER = {"eu": ["Holzwerke Münsterland GmbH", "Scierie des Ardennes SA"], "tropisch": ["Madeireira Rio Tapajós Ltda", "Sawmill Ogooué Timber SARL"], "nl": ["Bouwmaterialenhandel De IJsselkade"], "grijp": ["Technische Groothandel Oost BV"]}
BTW_INKOOP = {"eu": "BTW binnen de EU", "tropisch": "BTW buiten de EU", "nl": "BTW 21%", "grijp": "BTW 21%"}


def _magazijnen(bedrijf) -> dict:
	wortel = frappe.db.get_value("Warehouse", {"company": bedrijf.name, "is_group": 1, "parent_warehouse": ("in", ["", None])}, "name")
	uit = {}
	for sleutel, naam in (("hoofd", "Hoofdmagazijn"), ("zagerij", "Zagerij"), ("grijp", "Grijpvoorraad")):
		bestaand = frappe.db.get_value("Warehouse", {"company": bedrijf.name, "warehouse_name": naam}, "name")
		uit[sleutel] = bestaand or frappe.get_doc({"doctype": "Warehouse", "warehouse_name": naam, "company": bedrijf.name, "parent_warehouse": wortel}).insert().name
	return uit


def _artikelen() -> None:
	wortel = frappe.db.get_value("Item Group", {"is_group": 1, "parent_item_group": ("in", ["", None])}, "name")
	if not frappe.db.exists("Item Group", "Hout en plaatmateriaal"):
		frappe.get_doc({"doctype": "Item Group", "item_group_name": "Hout en plaatmateriaal", "parent_item_group": wortel, "is_group": 1}).insert()
	for groep in ("Naaldhout", "Loofhout", "Tropisch hardhout", "Plaatmateriaal", "Bevestiging en beslag"):
		if not frappe.db.exists("Item Group", groep):
			frappe.get_doc({"doctype": "Item Group", "item_group_name": groep, "parent_item_group": "Hout en plaatmateriaal"}).insert()
	for eenheid in ("m", "m³", "stuk"):
		if not frappe.db.exists("UOM", eenheid):
			frappe.get_doc({"doctype": "UOM", "uom_name": eenheid}).insert()
	for code, naam, groep, eenheid, kost, _opslag, soort, land, keurmerk, _aandeel in ARTIKELEN:
		if not frappe.db.exists("Item", code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": code,
					"item_name": naam,
					"description": f"{naam}, {keurmerk}",
					"item_group": groep,
					"stock_uom": eenheid,
					"is_stock_item": 1,
					"valuation_rate": kost,
					"valuation_method": "Moving Average",
					"country_of_origin": land,
					"keurmerk": keurmerk,
					# Tropisch hardhout per partij, met de herkomst op de partij.
					"has_batch_no": 1 if soort == "tropisch" else 0,
				}
			).insert()
	for code, naam, kost, _verbruik in GRIJP:
		if not frappe.db.exists("Item", code):
			frappe.get_doc({"doctype": "Item", "item_code": code, "item_name": naam, "item_group": "Bevestiging en beslag", "stock_uom": "stuk", "is_stock_item": 1, "valuation_rate": kost, "valuation_method": "Moving Average"}).insert()


def _partij(code: str, datum: datetime.date, land: str, leverancier: str | None, rng: random.Random) -> str:
	landcode = {"Gabon": "GA", "Brazil": "BR"}.get(land, "XX")
	naam = f"{code}-{datum:%y%m}-{landcode}"
	if not frappe.db.exists("Batch", naam):
		frappe.get_doc({"doctype": "Batch", "batch_id": naam, "item": code, "supplier": leverancier, "manufacturing_date": datum.isoformat(), "herkomst_land": land, "herkomst_gebied": rng.choice(GEBIEDEN.get(land, ["-"]))}).insert()
	return naam


def maak(rng: random.Random, bedrijf, klanten, leveranciers, jaren, vandaag) -> dict:
	"""De houthandel: projecten (raamcontracten en leveringen), en per maand inkoop, verkoop, zaagwerk en de telling
	van de grijpvoorraad, met de voorraad bijgehouden."""
	from openaec_bouw import demo

	tel = {"projecten": 0, "verkoop": 0, "inkoop": 0, "bank": 0, "afgeboekt": 0, "partijen": 0, "tellingen": 0, "zaagwerk": 0}
	frappe.db.set_value("Company", bedrijf.name, {"valuation_method": "Moving Average", "enable_perpetual_inventory": 1})
	# Partijen per artikel aan (voor de herkomst van tropisch hout), met de partij gewoon op de factuurregel.
	instellingen = frappe.get_doc("Stock Settings")
	instellingen.update({"enable_serial_and_batch_no_for_item": 1, "use_serial_batch_fields": 1, "valuation_method": "Moving Average"})
	instellingen.save()
	_artikelen()
	magazijn = _magazijnen(bedrijf)
	per_naam = {l.naam: l for l in leveranciers}
	artikel = {a[0]: frappe._dict(code=a[0], naam=a[1], eenheid=a[3], kost=a[4], prijs=round(a[4] * (a[5] + OPSLAG_EXTRA), 2), soort=a[6], land=a[7], aandeel=a[9]) for a in ARTIKELEN}
	eerste_dag = datetime.date(jaren[0], 1, 1)
	omzet_rekening, kost_rekening = demo._rek(bedrijf.name, "8050"), demo._rek(bedrijf.name, "7010")

	def verbruik(code: str, jaar: int, maand: int) -> float:
		"""Verwachte afzet van een artikel in een maand, in zijn eigen eenheid."""
		return bedrijf["jaren"][jaar][0] / 12 * SEIZOEN[maand - 1] * artikel[code].aandeel / artikel[code].prijs

	# Beginvoorraad: twee maanden afzet, tropisch hout in een openingspartij.
	voorraad, partijen, regels = {}, {}, []
	for code, a in artikel.items():
		aantal = round(verbruik(code, jaren[0], 1) * 2, 1 if a.eenheid == "m³" else 0)
		voorraad[code] = aantal
		regel = {"item_code": code, "warehouse": magazijn["hoofd"], "qty": aantal, "valuation_rate": a.kost}
		if a.soort == "tropisch":
			partij = _partij(code, eerste_dag - datetime.timedelta(days=45), a.land, None, rng)
			partijen[code] = [[partij, aantal]]
			regel.update({"batch_no": partij, "use_serial_batch_fields": 1})
			tel["partijen"] += 1
		regels.append(regel)
	grijp = {}
	for code, _naam, kost, per_kwartaal in GRIJP:
		grijp[code] = per_kwartaal * 1.5
		regels.append({"item_code": code, "warehouse": magazijn["grijp"], "qty": grijp[code], "valuation_rate": kost})
	if not frappe.db.exists("Stock Reconciliation", {"company": bedrijf.name, "purpose": "Opening Stock", "docstatus": ("<", 2)}):
		frappe.get_doc(
			{"doctype": "Stock Reconciliation", "company": bedrijf.name, "purpose": "Opening Stock", "posting_date": eerste_dag.isoformat(), "posting_time": "06:00:00", "set_posting_time": 1, "expense_account": demo._rek(bedrijf.name, "0510"), "items": regels}
		).insert()

	# De projecten: raamcontracten en leveringen op een werk, waar een deel van de verkoop aan hangt.
	werk, projecten = demo.WERK["hout"], []
	for i in range(bedrijf["projecten"]):
		jaar = [jaren[0] - 1, *jaren][i % (len(jaren) + 1)]
		klant = rng.choice([k for k in klanten if k.groep != "Particulier"])
		duur = rng.randint(*werk["duur"])
		start = datetime.date(jaar, 1, 1) + datetime.timedelta(days=rng.randint(0, 250) if jaar >= jaren[0] else rng.randint(200, 364))
		naam = rng.choice(werk["namen"]).format(p=rng.choice(demo.PLAATSEN), k=klant.naam)
		naam = f"{naam} ({bedrijf['afkorting']}-{jaar % 100}{i + 1:02d})"
		eind = start + datetime.timedelta(days=duur)
		bestaand = frappe.db.get_value("Project", {"project_name": naam}, "name")
		project = bestaand or frappe.get_doc(
			{
				"doctype": "Project",
				"project_name": naam,
				"company": bedrijf.name,
				"customer": klant.name,
				"project_type": next((t for t in werk["type"] if frappe.db.exists("Project Type", t)), None),
				"expected_start_date": start.isoformat(),
				"expected_end_date": eind.isoformat(),
				"status": "Completed" if eind < vandaag else "Open",
				"notes": demo.MERK,
			}
		).insert().name
		projecten.append(frappe._dict(name=project, klant=klant, start=start, eind=eind, naam=naam))
		tel["projecten"] += 1

	def inkoop(datum: datetime.date, soort: str, lijnen: list) -> None:
		"""Eén inkoopfactuur met ontvangst in het magazijn; `lijnen` = [(code, aantal, prijs, magazijn)]."""
		leverancier = per_naam[rng.choice(LEVERANCIER[soort])]
		sjabloon, belasting = demo._sjabloon("Purchase Taxes and Charges Template", bedrijf, BTW_INKOOP[soort])
		items = []
		for code, aantal, prijs, waar in lijnen:
			rij = {"item_code": code, "qty": aantal, "rate": prijs, "warehouse": waar, "expense_account": kost_rekening}
			if soort == "tropisch":
				partij = _partij(code, datum, artikel[code].land, leverancier.name, rng)
				partijen.setdefault(code, []).append([partij, aantal])
				rij.update({"batch_no": partij, "use_serial_batch_fields": 1})
				tel["partijen"] += 1
			items.append(rij)
		nummer = f"{datum.year}{rng.randint(10000, 99999)}"
		factuur = frappe.get_doc(
			{
				"doctype": "Purchase Invoice",
				"company": bedrijf.name,
				"supplier": leverancier.name,
				"posting_date": datum.isoformat(),
				"set_posting_time": 1,
				"posting_time": "08:00:00",
				"bill_no": nummer,
				"bill_date": datum.isoformat(),
				"due_date": (datum + datetime.timedelta(days=30)).isoformat(),
				"currency": "EUR",
				"conversion_rate": 1,
				"update_stock": 1,
				"taxes_and_charges": sjabloon,
				"taxes": belasting,
				"remarks": demo.MERK,
				"items": items,
			}
		).insert()
		pdf = demo._pdf(
			[
				leverancier.naam,
				"",
				f"FACTUUR {nummer}",
				f"Factuurdatum: {datum:%d-%m-%Y}",
				f"Aan: {bedrijf.name}",
				"",
				*[f"{flt(aantal):g} x {(artikel[code].naam if code in artikel else code)} à EUR {prijs:,.2f}" for code, aantal, prijs, _w in lijnen],
				"",
				f"Bedrag exclusief btw: EUR {flt(factuur.net_total):,.2f}",
				f"Totaal: EUR {flt(factuur.grand_total):,.2f}",
				"",
				"Dit is een verzonnen factuur in een demonstratieomgeving.",
			]
		)
		frappe.get_doc({"doctype": "File", "file_name": f"factuur-{nummer}.pdf", "attached_to_doctype": "Purchase Invoice", "attached_to_name": factuur.name, "content": pdf, "is_private": 1}).insert(ignore_permissions=True)
		tel["inkoop"] += 1
		betaald = datum + datetime.timedelta(days=rng.choice([14, 28, 30, 37]))
		if betaald <= vandaag:
			demo._bank(bedrijf, bedrijf.bank, betaald.isoformat(), False, factuur.grand_total, f"Factuur {nummer}", leverancier.naam, factuur.name)
			tel["bank"] += 1

	for jaar in jaren:
		for maand in range(1, 13):
			begin = datetime.date(jaar, maand, 1)
			if begin > vandaag:
				continue
			laatste = min(vandaag, (datetime.date(jaar + (maand == 12), maand % 12 + 1, 1) - datetime.timedelta(days=1)))
			# 1. Inkoop aan het begin van de maand: aanvullen wat onder anderhalve maand afzet komt.
			for soort in ("eu", "tropisch", "nl"):
				lijnen = []
				for code, a in artikel.items():
					nodig = verbruik(code, jaar, maand)
					if a.soort == soort and voorraad[code] < nodig * 1.5:
						aantal = round(nodig * 2.5, 1 if a.eenheid == "m³" else 0)
						lijnen.append((code, aantal, round(a.kost * rng.uniform(0.95, 1.06), 2), magazijn["hoofd"]))
						voorraad[code] += aantal
				if lijnen:
					inkoop(begin + datetime.timedelta(days=rng.randint(0, 3)), soort, lijnen)
			# 2. Zaagwerk: van eiken kwartiers naar geschaafde planken, met zaagverlies.
			if voorraad["EIK-P20140"] < verbruik("EIK-P20140", jaar, maand) * 1.5 and voorraad["EIK-K27"] >= 2:
				kuub = min(round(verbruik("EIK-P20140", jaar, maand) * 2 / 290, 1), voorraad["EIK-K27"] - 0.5)
				if kuub >= 0.5:
					meters = round(kuub * 290)
					frappe.get_doc(
						{
							"doctype": "Stock Entry",
							"stock_entry_type": "Repack",
							"purpose": "Repack",
							"company": bedrijf.name,
							"posting_date": (begin + datetime.timedelta(days=4)).isoformat(),
							"posting_time": "09:00:00",
							"set_posting_time": 1,
							"remarks": f"Zaagwerk: {kuub:g} m³ eiken kwartiers naar {meters} m planken ({demo.MERK})",
							"items": [
								{"item_code": "EIK-K27", "qty": kuub, "s_warehouse": magazijn["hoofd"]},
								{"item_code": "EIK-P20140", "qty": meters, "t_warehouse": magazijn["hoofd"], "is_finished_item": 1},
							],
						}
					).insert()
					voorraad["EIK-K27"] -= kuub
					voorraad["EIK-P20140"] += meters
					tel["zaagwerk"] += 1
			# 3. Verkoop, vanaf de zesde: nooit meer dan er ligt.
			doel = bedrijf["jaren"][jaar][0] / 12 * SEIZOEN[maand - 1]
			gewichten = [rng.uniform(0.4, 2.0) for _ in range(14)]
			lopend = [p for p in projecten if p.start <= laatste and p.eind >= begin]
			for gewicht in gewichten:
				dag = begin + datetime.timedelta(days=rng.randint(5, 27))
				if dag > vandaag:
					continue
				project = rng.choice(lopend) if lopend and rng.random() < 0.55 else None
				klant = project.klant if project else rng.choice(klanten)
				bedrag, items = doel * gewicht / sum(gewichten), []
				codes = rng.choices(list(artikel), weights=[a.aandeel for a in artikel.values()], k=rng.randint(1, 3))
				for code in dict.fromkeys(codes):
					a = artikel[code]
					aantal = min(round(bedrag / len(set(codes)) / a.prijs, 1 if a.eenheid == "m³" else 0), voorraad[code])
					if aantal <= 0:
						continue
					voorraad[code] -= aantal
					basis = {"item_code": code, "rate": a.prijs, "warehouse": magazijn["hoofd"], "income_account": omzet_rekening, "project": project.name if project else None}
					if a.soort == "tropisch":
						# Uit de oudste partij eerst; een regel per partij.
						rest = aantal
						while rest > 0 and partijen.get(code):
							partij = partijen[code][0]
							deel = min(rest, partij[1])
							items.append({**basis, "qty": deel, "batch_no": partij[0], "use_serial_batch_fields": 1})
							partij[1] -= deel
							rest = round(rest - deel, 3)
							if partij[1] <= 0:
								partijen[code].pop(0)
					else:
						items.append({**basis, "qty": aantal})
				if not items:
					continue
				sjabloon, belasting = demo._sjabloon("Sales Taxes and Charges Template", bedrijf, "BTW 21%")
				factuur = frappe.get_doc(
					{
						"doctype": "Sales Invoice",
						"company": bedrijf.name,
						"customer": klant.name,
						"posting_date": dag.isoformat(),
						"set_posting_time": 1,
						"posting_time": "14:00:00",
						"due_date": (dag + datetime.timedelta(days=30)).isoformat(),
						"currency": "EUR",
						"conversion_rate": 1,
						"update_stock": 1,
						"set_warehouse": magazijn["hoofd"],
						"project": project.name if project else None,
						"taxes_and_charges": sjabloon,
						"taxes": belasting,
						"remarks": demo.MERK,
						"items": items,
					}
				).insert()
				tel["verkoop"] += 1
				betaald = dag + datetime.timedelta(days=rng.choice([0, 0, 14, 21, 30, 34, 45]))
				if betaald <= vandaag:
					demo._bank(bedrijf, bedrijf.bank, betaald.isoformat(), True, factuur.grand_total, f"Betaling factuur {factuur.name}", klant.naam)
					tel["bank"] += 1
			# 4. Grijpvoorraad: per kwartaal aanvullen en tellen. Het verschil met de telling is het verbruik.
			if maand % 3 == 0 and laatste == datetime.date(jaar + (maand == 12), maand % 12 + 1, 1) - datetime.timedelta(days=1):
				lijnen = [(code, per_kwartaal, round(kost * rng.uniform(0.97, 1.05), 2), magazijn["grijp"]) for code, _n, kost, per_kwartaal in GRIJP]
				inkoop(datetime.date(jaar, maand - 2, 2), "grijp", lijnen)
	# De tellingen kunnen pas als er voorraad geboekt is: zie `tellingen`.
	if frappe.db.exists("Stock Ledger Entry", {"company": bedrijf.name}):
		tel["tellingen"] = tellingen(bedrijf, jaren, vandaag)
	return tel


def tellingen(bedrijf, jaren, vandaag) -> int:
	"""De telling van de grijpvoorraad aan het eind van elk kwartaal: het verschil met wat er zou moeten liggen is het
	verbruik en gaat naar de materiaalkosten. ERPNext neemt een telling tegen een kostenrekening pas aan als er
	voorraad geboekt is; dit draait dus ná het boeken van de beginvoorraad, niet in de conceptfase."""
	from openaec_bouw import demo

	magazijn, aantal = _magazijnen(bedrijf), 0
	stand = {code: per_kwartaal * 1.5 for code, _n, _k, per_kwartaal in GRIJP}
	for jaar in jaren:
		for kwartaal in range(1, 5):
			einde = datetime.date(jaar + (kwartaal == 4), (3 * kwartaal) % 12 + 1, 1) - datetime.timedelta(days=1)
			if einde > vandaag:
				continue
			rng, regels = random.Random(f"grijp-{jaar}-{kwartaal}"), []
			for code, _naam, kost, per_kwartaal in GRIJP:
				stand[code] = max(5, round(stand[code] + per_kwartaal - per_kwartaal * rng.uniform(0.85, 1.15)))
				regels.append({"item_code": code, "warehouse": magazijn["grijp"], "qty": stand[code], "valuation_rate": kost})
			if frappe.db.exists("Stock Reconciliation", {"company": bedrijf.name, "purpose": "Stock Reconciliation", "posting_date": einde.isoformat(), "docstatus": ("<", 2)}):
				continue
			frappe.get_doc(
				{"doctype": "Stock Reconciliation", "company": bedrijf.name, "purpose": "Stock Reconciliation", "posting_date": einde.isoformat(), "posting_time": "17:00:00", "set_posting_time": 1, "expense_account": demo._rek(bedrijf.name, "7010"), "items": regels}
			).insert()
			aantal += 1
	return aantal
