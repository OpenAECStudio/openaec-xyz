"""Demonstratiebedrijf: een verzonnen bouwgroep met een complete administratie over drie jaar.

Eén holding met zes werkmaatschappijen (aannemer, installateur met twee vestigingen, adviesbureau, sondeerbedrijf,
houthandel en materieelverhuur), elk met afdelingen, medewerkers, vijftien tot twintig projecten, verkoop- en
inkoopfacturen (met pdf), lonen, vaste kosten, banktransacties, afboekingen en btw-aangiftes per kwartaal.

    bench --site <site> execute openaec_bouw.demo.maak

Alles wordt als **concept** aangemaakt: er wordt niets geboekt. Het grootboek en de rapporten blijven dus leeg tot de
concepten geboekt zijn. De cijfers zijn zo gekozen dat er per bedrijf en per jaar winst of verlies uit komt
(`BEDRIJVEN[...]["jaren"]`). Alle namen, nummers en bedragen zijn verzonnen; dezelfde `zaad` geeft dezelfde gegevens.

Het script is herhaalbaar: wat er al staat, wordt overgeslagen, en een bedrijf dat al projecten heeft, krijgt geen
nieuwe administratie.
"""

import datetime
import random

import frappe
from frappe.utils import add_days, flt, getdate, today

from openaec_bouw import boekhouding

GROEP = "Noorderkade"
MERK = "Demonstratiegegevens OpenAEC"  # staat in de opmerking van elk document dat dit script maakt
BANK = "Demobank"

# Per bedrijf: `jaren` = (omzet, aandeel directe kosten) per jaar; `lonen` en `vast` per maand. Het resultaat volgt
# daaruit: omzet x (1 - direct) - 12 x (lonen x 1,32 + vast).
BEDRIJVEN = [
	{
		"sleutel": "holding",
		"naam": f"{GROEP} Holding BV",
		"afkorting": "NKH",
		"plaats": "Zwolle",
		"afdelingen": ["Directie", "Financiën", "Personeelszaken", "ICT"],
		"mensen": 6,
		"lonen": 31000,
		"vast": 9000,
		"jaren": {},
	},
	{
		"sleutel": "bouw",
		"naam": f"{GROEP} Bouw BV",
		"afkorting": "NKB",
		"plaats": "Zwolle",
		"afdelingen": ["Calculatie", "Werkvoorbereiding", "Uitvoering", "Timmerwerkplaats", "Administratie"],
		"mensen": 34,
		"lonen": 128000,
		"vast": 24000,
		"projecten": 20,
		"g_rekening": True,
		# 2024 verlies (twee werken liepen uit), daarna herstel.
		"jaren": {2024: (9_400_000, 0.78), 2025: (11_200_000, 0.745), 2026: (10_100_000, 0.735)},
	},
	{
		"sleutel": "installatie",
		"naam": f"{GROEP} Installatietechniek BV",
		"afkorting": "NKI",
		"plaats": "Zwolle",
		"vestigingen": ["Zwolle", "Deventer"],
		"afdelingen": ["Projecten", "Service en onderhoud", "Werkvoorbereiding", "Magazijn", "Administratie"],
		"mensen": 26,
		"lonen": 96000,
		"vast": 17000,
		"projecten": 18,
		"g_rekening": True,
		"jaren": {2024: (4_600_000, 0.56), 2025: (5_300_000, 0.585), 2026: (5_000_000, 0.55)},
	},
	{
		"sleutel": "advies",
		"naam": f"{GROEP} Advies BV",
		"afkorting": "NKA",
		"plaats": "Deventer",
		"afdelingen": ["Constructies", "Bouwfysica", "BIM en tekenwerk", "Projectleiding", "Administratie"],
		"mensen": 14,
		"lonen": 71000,
		"vast": 11000,
		"projecten": 18,
		# 2026 verlies: twee grote opdrachten vielen weg.
		"jaren": {2024: (1_650_000, 0.08), 2025: (1_720_000, 0.09), 2026: (1_180_000, 0.10)},
	},
	{
		"sleutel": "sonderingen",
		"naam": f"{GROEP} Sonderingen BV",
		"afkorting": "NKS",
		"plaats": "Kampen",
		"afdelingen": ["Veldwerk", "Laboratorium", "Geotechnisch advies", "Administratie"],
		"mensen": 9,
		"lonen": 38000,
		"vast": 4000,
		"projecten": 16,
		# 2025 verlies: de sondeerwagen stond drie maanden stil.
		"jaren": {2024: (1_020_000, 0.24), 2025: (760_000, 0.27), 2026: (930_000, 0.23)},
	},
	{
		"sleutel": "hout",
		"naam": f"{GROEP} Hout BV",
		"afkorting": "NKT",
		"plaats": "Kampen",
		"afdelingen": ["Verkoop", "Inkoop", "Zagerij", "Magazijn en expeditie", "Administratie"],
		"mensen": 12,
		"lonen": 44000,
		"vast": 16000,
		"projecten": 15,
		"jaren": {2024: (3_300_000, 0.745), 2025: (3_650_000, 0.73), 2026: (3_250_000, 0.74)},
	},
	{
		"sleutel": "materieel",
		"naam": f"{GROEP} Materieel BV",
		"afkorting": "NKM",
		"plaats": "Zwolle",
		"afdelingen": ["Verhuur", "Werkplaats en keuringen", "Transport", "Administratie"],
		"mensen": 8,
		"lonen": 31000,
		# Zonder de afschrijving: die komt uit het register van de vaste activa.
		"vast": 14000,
		"projecten": 15,
		"jaren": {2024: (1_450_000, 0.22), 2025: (1_580_000, 0.21), 2026: (1_400_000, 0.22)},
	},
]

PLAATSEN = ["Zwolle", "Deventer", "Kampen", "Apeldoorn", "Hattem", "Raalte", "Dalfsen", "Ommen", "Hardenberg", "Meppel", "Steenwijk", "Zutphen", "Epe", "Heerde", "Olst", "Wijhe", "Nunspeet", "Elburg", "Genemuiden", "Staphorst"]
STRATEN = ["Kade", "Dijkweg", "Marktstraat", "Stationsplein", "Lindelaan", "Havenweg", "Molenpad", "Parkweg", "Veerallee", "Bergweg", "Schoolstraat", "Industrieweg"]
VOORNAMEN_M = ["Daan", "Sem", "Lars", "Jeroen", "Bram", "Thijs", "Ruben", "Pieter", "Hans", "Erik", "Mark", "Kees", "Wout", "Niels", "Stefan", "Gerrit", "Arjan", "Mehmet", "Youssef", "Tom", "Jesse", "Rik", "Henk", "Bas"]
VOORNAMEN_V = ["Sanne", "Lotte", "Emma", "Anouk", "Marieke", "Fleur", "Ilse", "Karin", "Esther", "Naomi", "Femke", "Petra", "Judith", "Fatima", "Linda", "Roos"]
ACHTERNAMEN = ["de Vries", "Jansen", "van den Berg", "Bakker", "Visser", "Smit", "Meijer", "de Boer", "Mulder", "Bos", "Vos", "Peters", "Hendriks", "van Dijk", "Dekker", "Brouwer", "de Groot", "Kok", "Schouten", "Hoekstra", "Veenstra", "Koster", "Postma", "Kuipers", "Yilmaz", "El Amrani", "Wolters", "Nijland", "ten Brinke", "Oosterhuis"]

KLANTEN = [
	("Woonstichting De Veste", "Woningcorporatie"),
	("Woningbouwvereniging IJsselzicht", "Woningcorporatie"),
	("Stichting Wonen Salland", "Woningcorporatie"),
	("Gemeente Vechtdal", "Overheid"),
	("Gemeente Noordermeer", "Overheid"),
	("Waterschap Sallandse Weteringen", "Overheid"),
	("Provinciaal Vastgoedbedrijf Oost", "Overheid"),
	("Scholengroep De Wending", "Overheid"),
	("Zorggroep Het Hooge Veld", "Zakelijk"),
	("Kampereiland Vastgoed BV", "Zakelijk"),
	("Hanzepoort Ontwikkeling BV", "Zakelijk"),
	("Logistiek Centrum Hessenpoort BV", "Zakelijk"),
	("Zuivelcoöperatie Salland UA", "Zakelijk"),
	("Hotel De Gouden Karper BV", "Zakelijk"),
	("Vos & Dekker Makelaars", "Zakelijk"),
	("Autobedrijf Ter Horst BV", "Zakelijk"),
	("Tuincentrum De Esdoorn", "Zakelijk"),
	("Bakkerij Nijland VOF", "Zakelijk"),
	("Sportvereniging SV Wijhe", "Zakelijk"),
	("Huisartsenpraktijk De Linde", "Zakelijk"),
	("Aannemingsbedrijf Roelofs & Zn BV", "Aannemer"),
	("Bouwcombinatie Veluwerand VOF", "Aannemer"),
	("Timmerbedrijf Koster", "Aannemer"),
	("Bouwbedrijf Oosterhuis BV", "Aannemer"),
	("Architectenbureau Schouten & Mulder", "Architect en adviseur"),
	("Studio Bergweg Architecten", "Architect en adviseur"),
	("Fam. Hoekstra", "Particulier"),
	("Dhr. en mevr. Postma", "Particulier"),
	("Mevr. A. Wolters", "Particulier"),
	("Fam. Kuipers-Bos", "Particulier"),
	("Dhr. J. ten Brinke", "Particulier"),
	("Fam. Veenstra", "Particulier"),
	("Jachtbouw De Ketelhaven BV", "Zakelijk"),
	("Meubelmakerij Het Zwarte Water", "Zakelijk"),
]
# (naam, groep, land, soort kosten, g-rekening)
LEVERANCIERS = [
	("Betoncentrale Salland BV", "Materiaalleverancier", "Netherlands", "materiaal", False),
	("Bouwmaterialenhandel De IJsselkade", "Materiaalleverancier", "Netherlands", "materiaal", False),
	("Staalbouw Hessenweg BV", "Materiaalleverancier", "Netherlands", "materiaal", False),
	("Kozijnenfabriek Vechtstreek BV", "Materiaalleverancier", "Netherlands", "materiaal", False),
	("Technische Groothandel Oost BV", "Materiaalleverancier", "Netherlands", "materiaal", False),
	("Isolatie & Gevel Groothandel BV", "Materiaalleverancier", "Netherlands", "materiaal", False),
	("Holzwerke Münsterland GmbH", "Materiaalleverancier", "Germany", "hout_eu", False),
	("Scierie des Ardennes SA", "Materiaalleverancier", "Belgium", "hout_eu", False),
	("Madeireira Rio Tapajós Ltda", "Materiaalleverancier", "Brazil", "hout_tropisch", False),
	("Sawmill Ogooué Timber SARL", "Materiaalleverancier", "Gabon", "hout_tropisch", False),
	("Metselbedrijf Van der Kolk", "Onderaannemer", "Netherlands", "onderaanneming", True),
	("Stukadoorsbedrijf Brouwer VOF", "Onderaannemer", "Netherlands", "onderaanneming", True),
	("Dakdekkersbedrijf Hoogeveen BV", "Onderaannemer", "Netherlands", "onderaanneming", True),
	("Grondwerken Dekker BV", "Onderaannemer", "Netherlands", "onderaanneming", True),
	("Schildersbedrijf Meijer & Zn", "Onderaannemer", "Netherlands", "onderaanneming", True),
	("Tegelzetbedrijf Yilmaz", "Onderaannemer", "Netherlands", "onderaanneming", True),
	("Elektro Peters BV", "Onderaannemer", "Netherlands", "onderaanneming", True),
	("Steigerbouw Noordoost BV", "Verhuur materieel", "Netherlands", "huur", False),
	("Kraanverhuur De Hanze BV", "Verhuur materieel", "Netherlands", "huur", False),
	("Containerdienst Veluwe BV", "Verhuur materieel", "Netherlands", "afval", False),
	("Uitzendbureau Bouwkracht BV", "Zzp", "Netherlands", "inhuur", True),
	("Timmerman H. Kok (zzp)", "Zzp", "Netherlands", "inhuur", False),
	("Laboratorium Grondmechanica Oost BV", "Adviseur", "Netherlands", "onderaanneming", False),
	("Vastgoedbeheer De Stadsgracht BV", "Adviseur", "Netherlands", "huisvesting", False),
	("Leasemaatschappij Rijnstreek BV", "Adviseur", "Netherlands", "auto", False),
	("Verzekeringskantoor Salland", "Adviseur", "Netherlands", "verzekering", False),
	("Accountantskantoor Bos & Visser", "Adviseur", "Netherlands", "accountant", False),
	("Kantoorsoftware Hanze BV", "Adviseur", "Netherlands", "automatisering", False),
	("Energiebedrijf Oostland NV", "Adviseur", "Netherlands", "huisvesting", False),
	("Brandstofhandel De Kolk BV", "Adviseur", "Netherlands", "auto", False),
]
# soort kosten → (rekeningnummer, omschrijvingen)
KOSTEN = {
	"materiaal": ("7010", ["Betonmortel C30/37", "Kalkzandsteen en lijm", "Staalconstructie volgens tekening", "Kozijnen en deuren", "Isolatieplaten en folie", "Installatiemateriaal", "Dakpannen en panlatten", "Leidingwerk en appendages"]),
	"hout_eu": ("7010", ["Vuren C24 geschaafd", "Lariks Douglas balken", "Eiken kwartiers gezaagd", "Multiplex berken"]),
	"hout_tropisch": ("7010", ["Azobé damwandplanken FSC", "Meranti kozijnhout FSC", "Bankirai dekdelen FSC", "Padoek gezaagd FSC"]),
	"onderaanneming": ("7100", ["Metselwerk volgens opdracht", "Stukadoorswerk", "Dakbedekking en lood", "Grondwerk en riolering", "Schilderwerk", "Tegelwerk", "Elektrotechnische installatie", "Laboratoriumonderzoek monsters"]),
	"inhuur": ("7200", ["Inhuur timmerlieden week", "Inhuur grondwerkers week", "Inhuur monteurs week"]),
	"huur": ("7300", ["Huur steiger", "Huur torenkraan", "Huur verreiker", "Huur bouwlift"]),
	"afval": ("7400", ["Afvoer bouw- en sloopafval", "Afvoer grond", "Transport materieel"]),
	"huisvesting": ("4210", ["Huur bedrijfspand", "Gas, water en elektra"]),
	"auto": ("4300", ["Lease bedrijfsauto's", "Brandstof"]),
	"verzekering": ("4620", ["Verzekeringspremie CAR en aansprakelijkheid"]),
	"accountant": ("4610", ["Samenstellen jaarrekening en advies"]),
	"automatisering": ("4510", ["Licenties en beheer"]),
	"beheer": ("4600", ["Beheervergoeding holding: directie, financiën, personeelszaken en ICT"]),
}
# Per bedrijf: projecttype, omzetrekening, hoe er gefactureerd wordt, verdeling van de directe kosten en projectnamen.
WERK = {
	"bouw": {
		"type": ["Nieuwbouw", "Verbouw en renovatie", "Onderhoud"],
		"omzet": "8010",
		"termijnen": [0.30, 0.40, 0.25, 0.05],
		"kosten": {"materiaal": 0.42, "onderaanneming": 0.38, "inhuur": 0.08, "huur": 0.08, "afval": 0.04},
		"namen": ["Nieuwbouw {n} woningen {p}", "Renovatie {n} portiekwoningen {p}", "Uitbreiding basisschool {p}", "Verbouw kantoorpand {s} {p}", "Nieuwbouw bedrijfshal {p}", "Verduurzaming {n} huurwoningen {p}", "Aanbouw woonhuis {s} {p}", "Herstel gevels {s} {p}", "Nieuwbouw gezondheidscentrum {p}", "Transformatie pakhuis {s} {p}"],
		"duur": (120, 420),
	},
	"installatie": {
		"type": ["Nieuwbouw", "Onderhoud", "Verbouw en renovatie"],
		"omzet": "8010",
		"termijnen": [0.30, 0.40, 0.25, 0.05],
		"kosten": {"materiaal": 0.70, "onderaanneming": 0.18, "inhuur": 0.08, "huur": 0.04},
		"namen": ["Warmtepompen {n} woningen {p}", "Klimaatinstallatie kantoor {s} {p}", "Vervangen cv-ketels complex {p}", "Zonnepanelen bedrijfshal {p}", "Ventilatie basisschool {p}", "Elektra en data nieuwbouw {p}", "Onderhoudscontract installaties {p}", "Koelinstallatie zuivelfabriek {p}", "Laadpalen parkeerterrein {p}", "Sanitair en riolering hotel {p}"],
		"duur": (45, 240),
	},
	"advies": {
		"type": ["Advies en engineering"],
		"omzet": "8030",
		"termijnen": "maand",
		"kosten": {"onderaanneming": 1.0},
		"namen": ["Constructief ontwerp {n} woningen {p}", "Bouwfysisch advies school {p}", "BIM-coördinatie kantoor {p}", "Constructieberekening uitbouw {s} {p}", "Second opinion fundering {p}", "Brandveiligheidsadvies zorgcentrum {p}", "Engineering houtbouw {p}", "Energielabels complex {p}", "Draagkrachtanalyse parkeerdek {p}"],
		"duur": (60, 300),
	},
	"sonderingen": {
		"type": ["Advies en engineering", "Infra"],
		"omzet": "8030",
		"termijnen": [1.0],
		"kosten": {"onderaanneming": 0.55, "huur": 0.30, "afval": 0.15},
		"namen": ["Sonderingen nieuwbouw {p}", "Grondonderzoek dijkversterking {p}", "Funderingsadvies bedrijfshal {p}", "Peilbuizen en monitoring {p}", "Milieukundig bodemonderzoek {s} {p}", "Sonderingen windpark {p}", "Geotechnisch advies rotonde {p}"],
		"duur": (14, 90),
	},
	"hout": {
		"type": ["Intern", "Onderhoud"],
		"omzet": "8050",
		"termijnen": "maand",
		"kosten": {"hout_eu": 0.55, "hout_tropisch": 0.35, "afval": 0.10},
		"namen": ["Raamcontract houtlevering {k}", "Azobé damwand en remmingwerk {p}", "Gevelbekleding lariks {p}", "Hardhouten vlonders jachthaven {p}", "Kozijnhout meranti {k}", "Constructiehout nieuwbouw {p}", "Zaagwerk op maat {k}", "Bruggen en steigers azobé {p}"],
		"duur": (60, 330),
	},
	"materieel": {
		"type": ["Intern", "Onderhoud"],
		"omzet": "8040",
		"termijnen": "maand",
		"kosten": {"onderaanneming": 0.35, "materiaal": 0.40, "afval": 0.25},
		"namen": ["Verhuur torenkraan {p}", "Steigerwerk renovatie {p}", "Bouwplaatsinrichting {p}", "Verhuur verreikers {k}", "Keuringen materieel {k}", "Verhuur bouwketen {p}", "Hoogwerkers onderhoud {p}"],
		"duur": (30, 270),
	},
}
# Vaste kosten per maand: (soort, aandeel van `vast`, leverancier)
VAST = [
	("huisvesting", 0.42, "Vastgoedbeheer De Stadsgracht BV"),
	("auto", 0.30, "Leasemaatschappij Rijnstreek BV"),
	("automatisering", 0.12, "Kantoorsoftware Hanze BV"),
	("verzekering", 0.10, "Verzekeringskantoor Salland"),
	("accountant", 0.06, "Accountantskantoor Bos & Visser"),
]
# Vaste activa per bedrijf: (naam, categorie, aanschafwaarde, jaar van aanschaf). De categorie bepaalt de rekening en
# de levensduur.
CATEGORIEEN = {
	"Kranen en hijsmaterieel": ("0220", 10),
	"Verreikers en hoogwerkers": ("0220", 8),
	"Sondeermaterieel": ("0220", 8),
	"Steigers en bekisting": ("0250", 7),
	"Bouwketen en units": ("0230", 10),
	"Vervoermiddelen": ("0240", 6),
	"Machines werkplaats en zagerij": ("0220", 10),
}
ACTIVA = {
	"materieel": [
		("Torenkraan Liebherr 71 EC-B", "Kranen en hijsmaterieel", 412000, 2019),
		("Torenkraan Potain MDT 189", "Kranen en hijsmaterieel", 468000, 2022),
		("Mobiele bouwkraan Spierings SK597", "Kranen en hijsmaterieel", 695000, 2021),
		("Verreiker Manitou MT 1840", "Verreikers en hoogwerkers", 98000, 2020),
		("Verreiker Manitou MT 1440", "Verreikers en hoogwerkers", 84000, 2022),
		("Verreiker Merlo Roto 50.21", "Verreikers en hoogwerkers", 176000, 2023),
		("Hoogwerker JLG 600AJ", "Verreikers en hoogwerkers", 92000, 2019),
		("Hoogwerker Genie Z-45", "Verreikers en hoogwerkers", 71000, 2021),
		("Schaarhoogwerker Haulotte Compact 12 (4 stuks)", "Verreikers en hoogwerkers", 64000, 2022),
		("Steigermateriaal Layher Allround 6.000 m²", "Steigers en bekisting", 318000, 2020),
		("Steigermateriaal aanvulling 2.500 m²", "Steigers en bekisting", 141000, 2023),
		("Bouwketen en schaftunits (18 stuks)", "Bouwketen en units", 207000, 2018),
		("Sanitaire units (6 stuks)", "Bouwketen en units", 78000, 2021),
		("Vrachtwagen DAF CF met autolaadkraan", "Vervoermiddelen", 186000, 2021),
		("Dieplader Nooteboom", "Vervoermiddelen", 94000, 2019),
		("Bestelbus Mercedes Sprinter (2 stuks)", "Vervoermiddelen", 88000, 2022),
	],
	"sonderingen": [
		("Sondeertruck 200 kN op MAN 6x6", "Sondeermaterieel", 385000, 2018),
		("Sondeerrups 150 kN", "Sondeermaterieel", 214000, 2021),
		("Boorstelling Sonic", "Sondeermaterieel", 162000, 2022),
		("Laboratoriumapparatuur triaxiaal en samendrukking", "Sondeermaterieel", 96000, 2020),
		("Terreinwagen Toyota Hilux (2 stuks)", "Vervoermiddelen", 82000, 2022),
	],
	"bouw": [
		("Bedrijfsauto's uitvoering (9 stuks)", "Vervoermiddelen", 252000, 2021),
		("Machines timmerwerkplaats", "Machines werkplaats en zagerij", 186000, 2019),
		("Klein materieel en gereedschap", "Steigers en bekisting", 74000, 2022),
	],
	"installatie": [
		("Servicebussen (14 stuks)", "Vervoermiddelen", 448000, 2022),
		("Meet- en inregelapparatuur", "Machines werkplaats en zagerij", 62000, 2021),
	],
	"hout": [
		("Lintzaag en vierzijdige schaafmachine", "Machines werkplaats en zagerij", 268000, 2019),
		("Heftrucks en zijlader (4 stuks)", "Verreikers en hoogwerkers", 152000, 2021),
		("Vrachtwagen met kooiaap", "Vervoermiddelen", 164000, 2020),
	],
	"advies": [("Bedrijfsauto's (4 stuks)", "Vervoermiddelen", 128000, 2022)],
	"holding": [("Inventaris en automatisering hoofdkantoor", "Bouwketen en units", 96000, 2021)],
}
FUNCTIES = ["Projectleider", "Werkvoorbereider", "Calculator", "Uitvoerder", "Modelleur", "Constructeur", "Administratie"]


def _iban(rng: random.Random, bank: str = "DEMO") -> str:
	"""Een IBAN met kloppende controlecijfers en een bankcode die niet bestaat."""
	bban = bank + "".join(str(rng.randint(0, 9)) for _ in range(10))
	rest = int("".join(str(int(t, 36)) for t in bban + "NL00")) % 97
	return f"NL{98 - rest:02d}{bban}"


def _pdf(regels: list[str]) -> bytes:
	"""Een pdf van één pagina met deze regels tekst (zonder hulpprogramma: genoeg voor een voorbeeldfactuur)."""

	def veilig(t: str) -> str:
		return t.encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

	tekst = ["BT", "/F1 11 Tf", "14 TL", "56 790 Td"]
	for i, r in enumerate(regels):
		if i == 0:
			tekst += ["/F1 16 Tf", f"({veilig(r)}) Tj", "/F1 11 Tf", "T*"]
		else:
			tekst += [f"({veilig(r)}) Tj", "T*"]
	tekst.append("ET")
	stroom = "\n".join(tekst).encode("latin-1")
	objecten = [
		b"<< /Type /Catalog /Pages 2 0 R >>",
		b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
		b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
		b"<< /Length " + str(len(stroom)).encode() + b" >>\nstream\n" + stroom + b"\nendstream",
		b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
	]
	uit, plekken = b"%PDF-1.4\n", []
	for nr, inhoud in enumerate(objecten, start=1):
		plekken.append(len(uit))
		uit += f"{nr} 0 obj\n".encode() + inhoud + b"\nendobj\n"
	kruis = len(uit)
	uit += f"xref\n0 {len(objecten) + 1}\n0000000000 65535 f \n".encode()
	uit += b"".join(f"{p:010d} 00000 n \n".encode() for p in plekken)
	uit += f"trailer\n<< /Size {len(objecten) + 1} /Root 1 0 R >>\nstartxref\n{kruis}\n%%EOF\n".encode()
	return uit


def _rek(bedrijf: str, nummer: str) -> str:
	sleutel = (bedrijf, nummer)
	if sleutel not in frappe.flags.setdefault("oab_demo_rek", {}):
		frappe.flags.oab_demo_rek[sleutel] = frappe.db.get_value("Account", {"company": bedrijf, "account_number": nummer}, "name")
	return frappe.flags.oab_demo_rek[sleutel]


def _groep(doctype: str, naam: str) -> str:
	"""De groep met deze naam, of anders de hoofdgroep (als de module Basis hier niet aan staat)."""
	if frappe.db.exists(doctype, naam):
		return naam
	return frappe.db.get_value(doctype, {"is_group": 1, f"parent_{frappe.scrub(doctype)}": ("in", ["", None])}, "name")


def _boekjaren(jaren) -> None:
	for jaar in jaren:
		if not frappe.db.exists("Fiscal Year", {"year_start_date": f"{jaar}-01-01"}):
			frappe.get_doc({"doctype": "Fiscal Year", "year": str(jaar), "year_start_date": f"{jaar}-01-01", "year_end_date": f"{jaar}-12-31"}).insert()


def _bedrijven(rng: random.Random) -> dict:
	"""De groep zoals ERPNext hem bedoelt: eerst de holding als groepsbedrijf met het Nederlandse schema, daarna elke
	werkmaatschappij mét de holding als moeder. ERPNext kopieert dan het schema van de moeder, zodat alle bedrijven
	dezelfde rekeningen hebben en de geconsolideerde rapporten kloppen; `neem_schema_over` zet de RGS-codes, de
	standaardrekeningen en de btw-sjablonen erbij."""
	if not frappe.db.exists("Bank", BANK):
		frappe.get_doc({"doctype": "Bank", "bank_name": BANK}).insert()
	uit = {}
	holding = BEDRIJVEN[0]["naam"]
	for b in BEDRIJVEN:
		naam, is_holding = b["naam"], b["sleutel"] == "holding"
		if is_holding and frappe.db.exists("Company", naam) and frappe.db.get_value("Company", naam, "chart_of_accounts") != boekhouding.schema()["naam"]:
			boekhouding.zet_rekeningschema(naam)
			frappe.db.set_value("Company", naam, {"is_group": 1, "allow_account_creation_against_child_company": 1, "kvk_nummer": str(rng.randint(10000000, 99999999))})
		if not frappe.db.exists("Company", naam):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": naam,
					"abbr": b["afkorting"],
					"country": "Netherlands",
					"default_currency": "EUR",
					"is_group": 1 if is_holding else 0,
					"parent_company": None if is_holding else holding,
					"chart_of_accounts": "Standard" if is_holding else None,
					"allow_account_creation_against_child_company": 1 if is_holding else 0,
					"tax_id": f"NL{rng.randint(800000000, 899999999)}B01",
				}
			).insert()
			if is_holding:
				boekhouding.zet_rekeningschema(naam)
			else:
				boekhouding.neem_schema_over(naam)
			frappe.db.set_value("Company", naam, "kvk_nummer", str(rng.randint(10000000, 99999999)))
		rekeningen = {}
		for soort, nummer in (("bank", "1100"), ("g", "1150")):
			if soort == "g" and not b.get("g_rekening"):
				continue
			titel = f"{'G-rekening' if soort == 'g' else 'Betaalrekening'} {b['afkorting']}"
			bestaand = frappe.db.get_value("Bank Account", {"account_name": titel, "company": naam}, "name")
			rekeningen[soort] = bestaand or frappe.get_doc(
				{"doctype": "Bank Account", "account_name": titel, "bank": BANK, "is_company_account": 1, "company": naam, "account": _rek(naam, nummer), "iban": _iban(rng), "is_default": 1 if soort == "bank" else 0}
			).insert().name
		waarden = {"default_bank_account": rekeningen["bank"]}
		if "g" in rekeningen:
			waarden["g_rekening"] = rekeningen["g"]
		frappe.db.set_value("Company", naam, waarden)
		uit[b["sleutel"]] = frappe._dict(b, name=naam, bank=rekeningen["bank"], g=rekeningen.get("g"))
	return uit


def _activa(bedrijven: dict, eerste_jaar: int) -> dict:
	"""De vaste activa van elk bedrijf als register (concept), met wat er vóór het eerste boekjaar al is afgeschreven.
	Afschrijven: lineair per kwartaal tot tien procent restwaarde. Geeft per bedrijf de aanschafwaarde per rekening
	en de cumulatieve afschrijving terug, voor de beginbalans."""
	eerste_dag = datetime.date(eerste_jaar, 1, 1)
	for categorie, (nummer, _jaren) in CATEGORIEEN.items():
		doc = frappe.get_doc("Asset Category", categorie) if frappe.db.exists("Asset Category", categorie) else frappe.get_doc({"doctype": "Asset Category", "asset_category_name": categorie})
		staat = {r.company_name for r in doc.get("accounts")}
		for b in bedrijven.values():
			if b.name not in staat:
				doc.append("accounts", {"company_name": b.name, "fixed_asset_account": _rek(b.name, nummer), "accumulated_depreciation_account": _rek(b.name, "0290"), "depreciation_expense_account": _rek(b.name, "4110")})
		doc.save()
		if not frappe.db.exists("Item", categorie):
			frappe.get_doc({"doctype": "Item", "item_code": categorie, "item_name": categorie, "item_group": _groep("Item Group", "Materieel"), "stock_uom": next(e for e in ("stuk", "Nos", "Unit") if frappe.db.exists("UOM", e)), "is_stock_item": 0, "is_fixed_asset": 1, "asset_category": categorie}).insert()
	uit = {}
	for sleutel, b in bedrijven.items():
		frappe.db.set_value("Company", b.name, {"disposal_account": _rek(b.name, "8910"), "depreciation_cost_center": frappe.db.get_value("Company", b.name, "cost_center")})
		locatie = f"Terrein {b['plaats']}"
		if not frappe.db.exists("Location", locatie):
			frappe.get_doc({"doctype": "Location", "location_name": locatie}).insert()
		per_rekening, afgeschreven = {}, 0.0
		for naam, categorie, aanschaf, jaar in ACTIVA.get(sleutel, []):
			nummer, levensduur = CATEGORIEEN[categorie]
			termijnen = levensduur * 4
			in_gebruik = datetime.date(jaar, 7, 1)
			geboekt = min(termijnen - 1, max(0, ((eerste_dag.year - in_gebruik.year) * 12 + eerste_dag.month - in_gebruik.month) // 3))
			restwaarde = round(aanschaf * 0.10, 2)
			al = round((aanschaf - restwaarde) * geboekt / termijnen, 2)
			per_rekening[nummer] = per_rekening.get(nummer, 0) + aanschaf
			afgeschreven += al
			if frappe.db.exists("Asset", {"asset_name": naam, "company": b.name, "docstatus": ("<", 2)}):
				continue
			frappe.get_doc(
				{
					"doctype": "Asset",
					"asset_name": naam,
					"item_code": categorie,
					"asset_category": categorie,
					"company": b.name,
					"location": locatie,
					"asset_type": "Existing Asset",
					"purchase_date": in_gebruik.isoformat(),
					"available_for_use_date": in_gebruik.isoformat(),
					"net_purchase_amount": aanschaf,
					"purchase_amount": aanschaf,
					"asset_quantity": 1,
					"calculate_depreciation": 1,
					"opening_accumulated_depreciation": al,
					"opening_number_of_booked_depreciations": geboekt,
					"finance_books": [
						{"depreciation_method": "Straight Line", "total_number_of_depreciations": termijnen, "frequency_of_depreciation": 3, "depreciation_start_date": f"{eerste_jaar}-03-31", "expected_value_after_useful_life": restwaarde}
					],
				}
			).insert()
		uit[sleutel] = (per_rekening, round(afgeschreven, 2))
	return uit


def _fundament(rng: random.Random, bedrijven: dict, eerste_jaar: int) -> dict:
	"""Wat er moet staan vóór de eerste factuur, en wat later niet meer goed te zetten is:

	- een kostenplaats per vestiging (bij het installatiebedrijf), zodat het resultaat per vestiging te zien is;
	- de bedrijven van de groep als interne klant en interne leverancier van elkaar, voor onderlinge facturen;
	- de beginbalans per bedrijf op 1 januari van het eerste jaar (concept, als openingspost)."""
	tel = {"kostenplaatsen": 0, "interne_relaties": 0, "beginbalansen": 0}
	activa = _activa(bedrijven, eerste_jaar)
	tel["activa"] = frappe.db.count("Asset", {"company": ("in", [b.name for b in bedrijven.values()])})
	gebied = frappe.db.get_value("Territory", {"is_group": 0}, "name") or frappe.db.get_value("Territory", {}, "name")
	for b in bedrijven.values():
		hoofd = frappe.db.get_value("Cost Center", {"company": b.name, "is_group": 1}, "name")
		for vestiging in b.get("vestigingen", []):
			if hoofd and not frappe.db.exists("Cost Center", {"company": b.name, "cost_center_name": f"Vestiging {vestiging}"}):
				frappe.get_doc({"doctype": "Cost Center", "cost_center_name": f"Vestiging {vestiging}", "company": b.name, "parent_cost_center": hoofd}).insert()
				tel["kostenplaatsen"] += 1
		anderen = [{"company": a.name} for a in bedrijven.values() if a.name != b.name]
		if not frappe.db.exists("Customer", {"is_internal_customer": 1, "represents_company": b.name}):
			frappe.get_doc(
				{"doctype": "Customer", "customer_name": b.name, "customer_type": "Company", "customer_group": _groep("Customer Group", "Zakelijk"), "territory": gebied, "is_internal_customer": 1, "represents_company": b.name, "companies": anderen}
			).insert()
			tel["interne_relaties"] += 1
		if not frappe.db.exists("Supplier", {"is_internal_supplier": 1, "represents_company": b.name}):
			frappe.get_doc(
				{"doctype": "Supplier", "supplier_name": b.name, "supplier_group": _groep("Supplier Group", "Adviseur"), "country": "Netherlands", "is_internal_supplier": 1, "represents_company": b.name, "companies": anderen}
			).insert()
			tel["interne_relaties"] += 1
		if not frappe.db.exists("Journal Entry", {"company": b.name, "is_opening": "Yes", "docstatus": ("<", 2)}):
			# Geld op de bank naar de omvang van het bedrijf, de vaste activa uit het register, een lening naar de
			# boekwaarde, en het eigen vermogen als sluitpost.
			maand = b["lonen"] * 1.32 + b["vast"]
			bank = round(maand * rng.uniform(2.2, 3.4), -2)
			per_rekening, afgeschreven = activa[b.sleutel]
			boekwaarde = sum(per_rekening.values()) - afgeschreven
			lening = round(boekwaarde * {"materieel": 0.6, "sonderingen": 0.45}.get(b.sleutel, 0.25), -3)
			kapitaal = 18000
			regels = [("1100", bank, 0), *[(nummer, bedrag, 0) for nummer, bedrag in sorted(per_rekening.items())], ("0290", 0, afgeschreven), ("0710", 0, lening), ("0500", 0, kapitaal)]
			if b.sleutel == "holding":
				# De deelnemingen tegen het gestorte kapitaal van de werkmaatschappijen.
				regels.append(("0310", kapitaal * (len(bedrijven) - 1), 0))
			regels = [r for r in regels if r[1] or r[2]]
			regels.append(("0510", 0, round(sum(r[1] for r in regels) - sum(r[2] for r in regels), 2)))
			frappe.get_doc(
				{
					"doctype": "Journal Entry",
					"company": b.name,
					"posting_date": f"{eerste_jaar}-01-01",
					"voucher_type": "Opening Entry",
					"is_opening": "Yes",
					"user_remark": f"Beginbalans {eerste_jaar} ({MERK})",
					"accounts": [{"account": _rek(b.name, nr), "debit_in_account_currency": d, "credit_in_account_currency": c} for nr, d, c in regels],
				}
			).insert()
			tel["beginbalansen"] += 1
	return tel


def _mensen(rng: random.Random, bedrijven: dict) -> dict:
	"""Vestigingen, afdelingen en medewerkers per bedrijf. Geeft per bedrijf de medewerkers terug."""
	from openaec_bouw.demo_mensen import GEZICHTEN

	eigen_functies = {g[4] for mensen in GEZICHTEN.values() for g in mensen}
	for functie in sorted({*FUNCTIES, "Directeur", "Monteur", "Timmerman", "Magazijnmedewerker", "Chauffeur", "Sondeermeester", "Verkoper", *eigen_functies}):
		if not frappe.db.exists("Designation", functie):
			frappe.get_doc({"doctype": "Designation", "designation_name": functie}).insert()
	uit = {}
	for b in bedrijven.values():
		for vestiging in b.get("vestigingen", []):
			if not frappe.db.exists("Branch", vestiging):
				frappe.get_doc({"doctype": "Branch", "branch": vestiging}).insert()
		afdelingen = []
		for afdeling in b["afdelingen"]:
			naam = frappe.db.get_value("Department", {"department_name": afdeling, "company": b.name}, "name")
			afdelingen.append(naam or frappe.get_doc({"doctype": "Department", "department_name": afdeling, "company": b.name}).insert().name)
		bestaand = frappe.get_all("Employee", filters={"company": b.name}, pluck="name")
		gezichten = GEZICHTEN.get(b["sleutel"], [])
		per_afdeling = {frappe.db.get_value("Department", a, "department_name"): a for a in afdelingen}
		for nr in range(len(bestaand), b["mensen"]):
			if nr < len(gezichten):
				# De vaste gezichten van het bedrijf eerst, met hun eigen naam, functie en afdeling.
				voornaam, achternaam, geslacht, geboortejaar, functie, afdelingsnaam, in_dienst, _typering = gezichten[nr]
				afdeling = per_afdeling.get(afdelingsnaam, afdelingen[0])
				rng.random()
			else:
				vrouw = rng.random() < 0.28
				voornaam, achternaam, geslacht = rng.choice(VOORNAMEN_V if vrouw else VOORNAMEN_M), rng.choice(ACHTERNAMEN), "Female" if vrouw else "Male"
				afdeling = rng.choice(afdelingen)
				functie = rng.choice(_functies(b["sleutel"], afdeling))
				geboortejaar, in_dienst = rng.randint(1964, 2003), rng.randint(2009, 2024)
			medewerker = {
				"doctype": "Employee",
				"first_name": voornaam,
				"last_name": achternaam,
				"gender": geslacht,
				"date_of_birth": f"{geboortejaar}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
				"date_of_joining": f"{max(in_dienst, geboortejaar + 17)}-{rng.randint(1, 12):02d}-01",
				"company": b.name,
				"department": afdeling,
				"designation": functie,
				"status": "Active",
			}
			if b.get("vestigingen"):
				medewerker["branch"] = b["vestigingen"][nr % len(b["vestigingen"])]
			bestaand.append(frappe.get_doc(medewerker).insert().name)
		uit[b.sleutel] = bestaand
	return uit


def _hierarchie(bedrijven: dict) -> int:
	"""Wie aan wie rapporteert: elke afdeling heeft een hoofd (wie er het langst werkt, of het vaste gezicht van die
	afdeling), de medewerkers rapporteren aan hun afdelingshoofd, de hoofden aan de directeur van het bedrijf en de
	directeuren aan de directeur van de holding."""
	gezet = 0

	def zet(medewerker: str, baas: str | None) -> None:
		nonlocal gezet
		if baas and baas != medewerker and frappe.db.get_value("Employee", medewerker, "reports_to") != baas:
			doc = frappe.get_doc("Employee", medewerker)
			doc.reports_to = baas
			doc.save()
			gezet += 1

	def directeur(bedrijf: str) -> str | None:
		return frappe.db.get_value("Employee", {"company": bedrijf, "designation": "Directeur"}, "name", order_by="date_of_joining asc")

	top = directeur(bedrijven["holding"].name)
	for sleutel, b in bedrijven.items():
		baas = directeur(b.name)
		if sleutel != "holding":
			zet(baas, top)
		for afdeling in frappe.get_all("Department", filters={"company": b.name}, pluck="name"):
			leden = frappe.get_all("Employee", filters={"company": b.name, "department": afdeling}, fields=["name", "designation"], order_by="date_of_joining asc, name asc")
			if not leden:
				continue
			hoofd = next((m.name for m in leden if m.name == baas), leden[0].name)
			zet(hoofd, baas)
			for m in leden:
				zet(m.name, hoofd)
	return gezet


def _functies(sleutel: str, afdeling: str) -> list[str]:
	if "Administratie" in afdeling or "Financiën" in afdeling:
		return ["Administratie"]
	return {
		"bouw": ["Timmerman", "Uitvoerder", "Werkvoorbereider", "Calculator", "Projectleider"],
		"installatie": ["Monteur", "Monteur", "Werkvoorbereider", "Projectleider", "Magazijnmedewerker"],
		"advies": ["Constructeur", "Modelleur", "Projectleider"],
		"sonderingen": ["Sondeermeester", "Constructeur"],
		"hout": ["Verkoper", "Magazijnmedewerker", "Chauffeur"],
		"materieel": ["Monteur", "Chauffeur", "Verkoper"],
	}.get(sleutel, ["Administratie"])


def _relaties(rng: random.Random) -> tuple[list, list]:
	gebied = frappe.db.get_value("Territory", {"is_group": 0}, "name") or frappe.db.get_value("Territory", {}, "name")
	klanten = []
	for naam, groep in KLANTEN:
		bestaand = frappe.db.get_value("Customer", {"customer_name": naam}, "name")
		klanten.append(
			frappe._dict(
				name=bestaand
				or frappe.get_doc(
					{
						"doctype": "Customer",
						"customer_name": naam,
						"customer_type": "Individual" if groep == "Particulier" else "Company",
						"customer_group": _groep("Customer Group", groep),
						"territory": gebied,
						"tax_id": None if groep == "Particulier" else f"NL{rng.randint(800000000, 899999999)}B01",
					}
				).insert().name,
				naam=naam,
				groep=groep,
			)
		)
	leveranciers = []
	for naam, groep, land, soort, g in LEVERANCIERS:
		bestaand = frappe.db.get_value("Supplier", {"supplier_name": naam}, "name")
		if not bestaand:
			doc = {"doctype": "Supplier", "supplier_name": naam, "supplier_group": _groep("Supplier Group", groep), "country": land}
			if land == "Netherlands":
				doc["tax_id"] = f"NL{rng.randint(800000000, 899999999)}B01"
			if g:
				doc.update({"g_rekening_iban": _iban(rng, "GDEM"), "g_percentage": rng.choice([25, 30, 35, 40])})
			bestaand = frappe.get_doc(doc).insert().name
			if land == "Netherlands":
				frappe.get_doc({"doctype": "Bank Account", "account_name": naam[:120], "bank": BANK, "party_type": "Supplier", "party": bestaand, "iban": _iban(rng), "is_default": 1}).insert()
		leveranciers.append(frappe._dict(name=bestaand, naam=naam, land=land, soort=soort))
	return klanten, leveranciers


def _artikel(naam: str) -> str:
	if not frappe.db.exists("Item", naam):
		groep = _groep("Item Group", "Advies en diensten")
		eenheid = next(e for e in ("post", "stuk", "Nos", "Unit") if frappe.db.exists("UOM", e))
		frappe.get_doc({"doctype": "Item", "item_code": naam, "item_name": naam, "item_group": groep, "stock_uom": eenheid, "is_stock_item": 0, "is_sales_item": 1, "is_purchase_item": 1}).insert()
	return naam


def _sjabloon(doctype: str, bedrijf: frappe._dict, titel: str) -> tuple[str | None, list]:
	"""Het btw-sjabloon met deze titel bij het bedrijf, met de regels klaar om op een factuur te zetten."""
	sleutel = (doctype, bedrijf.name, titel)
	if sleutel not in frappe.flags.setdefault("oab_demo_btw", {}):
		naam = frappe.db.get_value(doctype, {"company": bedrijf.name, "title": titel}, "name")
		regels = []
		if naam:
			regels = [{k: v for k, v in r.items() if k not in ("name", "parent", "parentfield", "parenttype", "idx", "creation", "modified", "owner", "modified_by", "docstatus")} for r in frappe.get_doc(doctype, naam).as_dict()["taxes"]]
		frappe.flags.oab_demo_btw[sleutel] = (naam, regels)
	naam, regels = frappe.flags.oab_demo_btw[sleutel]
	return naam, [dict(r) for r in regels]


def _verkoop(bedrijf, klant, datum, project, regels, rekening, btw="BTW 21%", g_bedrag=0) -> frappe._dict:
	sjabloon, belasting = _sjabloon("Sales Taxes and Charges Template", bedrijf, btw)
	factuur = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"company": bedrijf.name,
			"customer": klant.name,
			"posting_date": datum,
			"set_posting_time": 1,
			"due_date": add_days(datum, 30),
			"currency": "EUR",
			"conversion_rate": 1,
			"project": project,
			"taxes_and_charges": sjabloon,
			"taxes": belasting,
			"remarks": MERK,
			"g_bedrag": g_bedrag,
			"items": [{"item_code": _artikel(artikel), "description": tekst, "qty": 1, "rate": bedrag, "income_account": _rek(bedrijf.name, rekening), "project": project} for artikel, tekst, bedrag in regels],
		}
	)
	factuur.insert()
	return factuur


def _inkoop(rng, bedrijf, leverancier, datum, project, soort, bedrag, bijlage: bool = True, tegenfactuur: str | None = None) -> frappe._dict:
	nummer, teksten = KOSTEN[soort]
	titel = {"hout_eu": "BTW binnen de EU", "hout_tropisch": "BTW buiten de EU"}.get(soort)
	if not titel:
		titel = "BTW verlegd" if soort == "onderaanneming" and bedrijf.sleutel in ("bouw", "installatie") and rng.random() < 0.7 else "BTW 21%"
	sjabloon, belasting = _sjabloon("Purchase Taxes and Charges Template", bedrijf, titel)
	tekst = rng.choice(teksten)
	factuurnummer = tegenfactuur or f"{datum[:4]}{rng.randint(10000, 99999)}"
	factuur = frappe.get_doc(
		{
			"doctype": "Purchase Invoice",
			"company": bedrijf.name,
			"supplier": leverancier.name,
			"posting_date": datum,
			"set_posting_time": 1,
			"bill_no": factuurnummer,
			"bill_date": datum,
			"due_date": add_days(datum, 30),
			"currency": "EUR",
			"conversion_rate": 1,
			"project": project,
			"taxes_and_charges": sjabloon,
			"taxes": belasting,
			"remarks": MERK,
			"inter_company_invoice_reference": tegenfactuur,
			"items": [{"item_code": _artikel("Inkoop " + soort.replace("_", " ")), "description": tekst, "qty": 1, "rate": bedrag, "expense_account": _rek(bedrijf.name, nummer), "project": project}],
		}
	)
	factuur.insert()
	if bijlage:
		pdf = _pdf(
			[
				leverancier.naam,
				"",
				f"FACTUUR {factuurnummer}",
				f"Factuurdatum: {getdate(datum).strftime('%d-%m-%Y')}",
				f"Aan: {bedrijf.name}",
				f"Uw referentie: {project or '-'}",
				"",
				f"Omschrijving: {tekst}",
				f"Bedrag exclusief btw: EUR {flt(factuur.net_total):,.2f}",
				f"Btw ({titel}): EUR {flt(factuur.total_taxes_and_charges):,.2f}",
				f"Totaal: EUR {flt(factuur.grand_total):,.2f}",
				"",
				"Betaling binnen 30 dagen onder vermelding van het factuurnummer.",
				"",
				"Dit is een verzonnen factuur in een demonstratieomgeving.",
			]
		)
		frappe.get_doc({"doctype": "File", "file_name": f"factuur-{factuurnummer}.pdf", "attached_to_doctype": "Purchase Invoice", "attached_to_name": factuur.name, "content": pdf, "is_private": 1}).insert(ignore_permissions=True)
	return factuur


def _bank(bedrijf, rekening, datum, bij: bool, bedrag, omschrijving, naam="", kenmerk="") -> None:
	frappe.get_doc(
		{
			"doctype": "Bank Transaction",
			"date": datum,
			"bank_account": rekening,
			"company": bedrijf.name,
			"currency": "EUR",
			"deposit": flt(bedrag, 2) if bij else 0,
			"withdrawal": 0 if bij else flt(bedrag, 2),
			"description": omschrijving,
			"reference_number": kenmerk,
			"bank_party_name": naam[:140],
			"transaction_id": frappe.generate_hash(length=16),
		}
	).insert()


def _journaal(bedrijf, datum, tekst, regels) -> None:
	"""Een concept-journaalpost; `regels` = [(rekeningnummer, debet, credit)], eventueel met (partijtype, partij) erbij."""
	accounts = []
	for regel in regels:
		rij = {"account": _rek(bedrijf.name, regel[0]), "debit_in_account_currency": flt(regel[1], 2), "credit_in_account_currency": flt(regel[2], 2)}
		if len(regel) > 3:
			rij.update({"party_type": regel[3], "party": regel[4]})
		accounts.append(rij)
	frappe.get_doc({"doctype": "Journal Entry", "company": bedrijf.name, "posting_date": datum, "voucher_type": "Journal Entry", "user_remark": f"{tekst} ({MERK})", "accounts": accounts}).insert()


def _datum(d: datetime.date) -> str:
	return d.isoformat()


def _projecten(rng, bedrijf, klanten, leveranciers, medewerkers, jaren, vandaag) -> dict:
	"""De projecten van één bedrijf met hun verkoop- en inkoopfacturen en de bankregels van de betalingen."""
	werk = WERK[bedrijf.sleutel]
	tel = {"projecten": 0, "verkoop": 0, "inkoop": 0, "bank": 0, "afgeboekt": 0}
	per_soort = {}
	for l in leveranciers:
		per_soort.setdefault(l.soort, []).append(l)
	zakelijk = [k for k in klanten if k.groep != "Particulier"]
	aantal = bedrijf["projecten"]
	# De projecten verdeeld over de jaren, met de omzet van het jaar verdeeld naar een willekeurig gewicht.
	# Ook projecten die het jaar ervoor begonnen: zo loopt er vanaf de eerste dag werk door en schuift de omzet niet
	# scheef. Van die projecten komen alleen de facturen vanaf het eerste boekjaar in de administratie.
	eerste_dag = datetime.date(jaren[0], 1, 1)
	startjaren = [jaren[0] - 1, *jaren]
	plan = []
	for i in range(aantal):
		plan.append((startjaren[i % len(startjaren)], rng.uniform(0.4, 2.2)))
	for jaar in startjaren:
		gewichten = sum(g for j, g in plan if j == jaar)
		omzet_jaar, direct = bedrijf["jaren"][max(jaar, jaren[0])]
		if jaar < jaren[0]:
			# Alleen het deel dat doorloopt telt: bij kort werk weinig, bij werk van een jaar ruim de helft.
			omzet_jaar *= min(1.0, sum(werk["duur"]) / 2 / 365) * 0.6
		for j, gewicht in [p for p in plan if p[0] == jaar]:
			som = round(omzet_jaar * gewicht / gewichten, -2)
			klant = rng.choice(klanten if bedrijf.sleutel in ("bouw", "hout", "installatie") else zakelijk)
			duur = rng.randint(*werk["duur"])
			# Een project van vóór het eerste jaar begint laat genoeg om er nog in door te lopen.
			start = datetime.date(jaar, 1, 1) + datetime.timedelta(days=rng.randint(0, 250) if jaar >= jaren[0] else rng.randint(max(120, 364 - duur + 20), 364))
			eind = start + datetime.timedelta(days=duur)
			naam = rng.choice(werk["namen"]).format(n=rng.choice([6, 8, 12, 16, 24, 32, 48]), p=rng.choice(PLAATSEN), s=rng.choice(STRATEN), k=klant.naam)
			naam = f"{naam} ({bedrijf['afkorting']}-{jaar % 100}{tel['projecten'] + 1:02d})"
			if frappe.db.exists("Project", {"project_name": naam}):
				continue
			project = {
				"doctype": "Project",
				"project_name": naam,
				"company": bedrijf.name,
				"customer": klant.name,
				"project_type": next((t for t in werk["type"] if frappe.db.exists("Project Type", t)), None),
				"expected_start_date": _datum(start),
				"expected_end_date": _datum(eind),
				"estimated_costing": round(som * direct, 2),
				"aanneemsom": som,
				"status": "Completed" if eind < vandaag else "Open",
				"notes": MERK,
			}
			if medewerkers and frappe.get_meta("Project").has_field("custom_project_manager"):
				project["custom_project_manager"] = rng.choice(medewerkers[: max(3, len(medewerkers) // 4)])
			project = frappe.get_doc(project).insert().name
			tel["projecten"] += 1

			# Verkoop: termijnen volgens de staat, of elke maand een deel.
			if werk["termijnen"] == "maand":
				maanden = max(1, duur // 30)
				momenten = [(start + datetime.timedelta(days=30 * (m + 1)), 1 / maanden, f"Declaratie maand {m + 1}") for m in range(maanden)]
			else:
				stappen = werk["termijnen"]
				teksten = ["Termijn bij opdracht", "Termijn bij start uitvoering", "Termijn bij oplevering", "Termijn na onderhoudstermijn"]
				momenten = [(start + datetime.timedelta(days=int(duur * i / max(1, len(stappen) - 1)) if len(stappen) > 1 else duur), deel, teksten[i] if len(stappen) > 1 else "Factuur na uitvoering") for i, deel in enumerate(stappen)]
			particulier = klant.groep == "Particulier"
			btw = "BTW verlegd" if klant.groep == "Aannemer" and bedrijf.sleutel in ("bouw", "installatie") else ("BTW 9%" if particulier and bedrijf.sleutel == "bouw" and "erbouw" in naam else "BTW 21%")
			# Een op de vijftien klanten betaalt de laatste factuur niet: die wordt afgeboekt.
			wanbetaler = rng.random() < 0.07
			for nr, (moment, deel, tekst) in enumerate(momenten):
				if moment > vandaag or moment < eerste_dag:
					continue
				bedrag = round(som * deel, 2)
				# De directe kosten bij deze termijn, in de weken ervoor: zo volgt het resultaat de omzet.
				aandeel_direct = bedrijf["jaren"].get(moment.year, (0, direct))[1]
				for soort, aandeel in werk["kosten"].items():
					kosten = round(bedrag * aandeel_direct * aandeel * rng.uniform(0.95, 1.05), 2)
					if kosten < 250:
						continue
					kostdatum = max(eerste_dag, start, moment - datetime.timedelta(days=rng.randint(3, 40)))
					leverancier = rng.choice(per_soort.get(soort) or per_soort["materiaal"])
					inkoop = _inkoop(rng, bedrijf, leverancier, _datum(kostdatum), project, soort, kosten)
					tel["inkoop"] += 1
					voldaan = kostdatum + datetime.timedelta(days=rng.choice([14, 28, 30, 30, 37]))
					if voldaan <= vandaag:
						g = flt(inkoop.get("g_bedrag"), 2)
						if g:
							_bank(bedrijf, bedrijf.bank, _datum(voldaan), False, g, f"Factuur {inkoop.bill_no} G-rekening", leverancier.naam, f"{inkoop.name}-G")
							tel["bank"] += 1
						_bank(bedrijf, bedrijf.bank, _datum(voldaan), False, flt(inkoop.grand_total - g, 2), f"Factuur {inkoop.bill_no}", leverancier.naam, inkoop.name)
						tel["bank"] += 1
				g_bedrag = round(bedrag * 0.3, 2) if bedrijf.get("g") and klant.groep == "Aannemer" else 0
				factuur = _verkoop(bedrijf, klant, _datum(moment), project, [("Aanneemsom termijn" if werk["termijnen"] != "maand" else "Declaratie", f"{tekst}: {naam}", bedrag)], werk["omzet"], btw, g_bedrag)
				tel["verkoop"] += 1
				laatste = nr == len(momenten) - 1
				betaald = moment + datetime.timedelta(days=rng.choice([12, 21, 28, 30, 34, 45, 61]))
				if wanbetaler and laatste and moment < vandaag - datetime.timedelta(days=150):
					afboeken = moment + datetime.timedelta(days=150)
					_journaal(bedrijf, _datum(afboeken), f"Afboeking oninbare vordering {factuur.name}", [("4910", factuur.grand_total, 0), ("1310", 0, factuur.grand_total, "Customer", klant.name)])
					tel["afgeboekt"] += 1
				elif betaald <= vandaag:
					totaal = flt(factuur.grand_total, 2)
					if g_bedrag:
						_bank(bedrijf, bedrijf.g, _datum(betaald), True, g_bedrag, f"Factuur {factuur.name} G-rekening", klant.naam)
						totaal = flt(totaal - g_bedrag, 2)
						tel["bank"] += 1
					_bank(bedrijf, bedrijf.bank, _datum(betaald), True, totaal, f"Betaling factuur {factuur.name} {naam[:60]}", klant.naam)
					tel["bank"] += 1
			# Meerwerk op een deel van de projecten.
			if rng.random() < 0.35 and eerste_dag <= eind <= vandaag and bedrijf.sleutel in ("bouw", "installatie"):
				meerwerk = _verkoop(bedrijf, klant, _datum(eind), project, [("Meerwerk", f"Meerwerk volgens opdrachtbevestiging: {naam}", round(som * rng.uniform(0.02, 0.07), 2))], "8020", btw)
				tel["verkoop"] += 1
				if eind + datetime.timedelta(days=30) <= vandaag:
					_bank(bedrijf, bedrijf.bank, _datum(eind + datetime.timedelta(days=30)), True, meerwerk.grand_total, f"Betaling factuur {meerwerk.name} meerwerk", klant.naam)
					tel["bank"] += 1

	return tel


def _vaste_lasten(rng, bedrijf, leveranciers, jaren, vandaag) -> dict:
	"""Per maand de lonen (journaalpost en betaling) en de vaste kosten (inkoopfacturen met pdf)."""
	tel = {"lonen": 0, "inkoop": 0, "bank": 0}
	per_naam = {l.naam: l for l in leveranciers}
	for jaar in jaren:
		for maand in range(1, 13):
			einde = datetime.date(jaar, maand, 25)
			if einde > vandaag:
				continue
			bruto = round(bedrijf["lonen"] * rng.uniform(0.97, 1.03) * (1 + 0.03 * (jaar - jaren[0])), 2)
			sociaal, pensioen = round(bruto * 0.19, 2), round(bruto * 0.13, 2)
			heffing = round(bruto * 0.31 + sociaal, 2)
			netto = round(bruto - bruto * 0.31 - pensioen * 0.4, 2)
			afdracht_pensioen = round(bruto + sociaal + pensioen - heffing - netto, 2)
			_journaal(
				bedrijf,
				_datum(einde),
				f"Loonjournaalpost {maand:02d}-{jaar}",
				[("4010", bruto, 0), ("4020", sociaal, 0), ("4030", pensioen, 0), ("1720", 0, netto), ("1700", 0, heffing), ("1710", 0, afdracht_pensioen)],
			)
			tel["lonen"] += 1
			_bank(bedrijf, bedrijf.bank, _datum(einde), False, netto, f"Salarissen {maand:02d}-{jaar}", "Verzamelbetaling lonen")
			_bank(bedrijf, bedrijf.bank, _datum(einde + datetime.timedelta(days=30)), False, heffing, f"Loonheffing {maand:02d}-{jaar}", "Belastingdienst") if einde + datetime.timedelta(days=30) <= vandaag else None
			tel["bank"] += 2
			for soort, aandeel, naam in VAST:
				# Verzekering en accountant per kwartaal, de rest per maand.
				per_kwartaal = soort in ("verzekering", "accountant")
				if per_kwartaal and maand % 3 != 1:
					continue
				bedrag = round(bedrijf["vast"] * aandeel * (3 if per_kwartaal else 1) * rng.uniform(0.98, 1.02), 2)
				moment = datetime.date(jaar, maand, rng.randint(1, 8))
				factuur = _inkoop(rng, bedrijf, per_naam[naam], _datum(moment), None, soort, bedrag)
				tel["inkoop"] += 1
				if moment + datetime.timedelta(days=21) <= vandaag:
					_bank(bedrijf, bedrijf.bank, _datum(moment + datetime.timedelta(days=21)), False, factuur.grand_total, f"Factuur {factuur.bill_no}", naam, factuur.name)
					tel["bank"] += 1
	return tel


def _beheervergoeding(bedrijven: dict, jaren, vandaag) -> int:
	"""De holding belast haar kosten per maand door aan de werkmaatschappijen, naar de omvang van hun loonsom: een
	verkoopfactuur bij de holding aan de interne klant en de inkoopfactuur bij de werkmaatschappij van de interne
	leverancier, aan elkaar gekoppeld."""
	holding = bedrijven["holding"]
	if frappe.db.exists("Sales Invoice", {"company": holding.name, "remarks": MERK, "docstatus": ("<", 2)}):
		return 0
	dochters = [b for sleutel, b in bedrijven.items() if sleutel != "holding"]
	loonsom = sum(b["lonen"] for b in dochters)
	per_maand = (holding["lonen"] * 1.32 + holding["vast"]) * 1.04
	leverancier = frappe._dict(name=frappe.db.get_value("Supplier", {"is_internal_supplier": 1, "represents_company": holding.name}, "name"), naam=holding.name, land="Netherlands", soort="beheer")
	rng, aantal = random.Random("beheer"), 0
	for jaar in jaren:
		for maand in range(1, 13):
			datum = datetime.date(jaar, maand, 28)
			if datum > vandaag:
				continue
			for b in dochters:
				bedrag = round(per_maand * b["lonen"] / loonsom, 2)
				klant = frappe._dict(name=frappe.db.get_value("Customer", {"is_internal_customer": 1, "represents_company": b.name}, "name"), naam=b.name)
				verkoop = _verkoop(holding, klant, _datum(datum), None, [("Beheervergoeding", f"Beheervergoeding {maand:02d}-{jaar}", bedrag)], "8910")
				_inkoop(rng, b, leverancier, _datum(datum), None, "beheer", bedrag, tegenfactuur=verkoop.name)
				aantal += 1
	return aantal


def _onderhanden_werk(bedrijf, jaren, vandaag) -> int:
	"""Per kwartaaleinde de stand van het onderhanden werk (concept, met de conceptfacturen meegeteld) en de
	journaalpost met de mutatie."""
	aantal = 0
	for jaar in jaren:
		for kwartaal in range(1, 5):
			peildatum = datetime.date(jaar + (kwartaal == 4), (3 * kwartaal) % 12 + 1, 1) - datetime.timedelta(days=1)
			if peildatum >= vandaag or frappe.db.exists("Onderhanden Werk", {"bedrijf": bedrijf.name, "peildatum": _datum(peildatum), "docstatus": ("<", 2)}):
				continue
			stand = frappe.get_doc({"doctype": "Onderhanden Werk", "bedrijf": bedrijf.name, "peildatum": _datum(peildatum), "methode": "Naar voortgang", "concepten_meetellen": 1, "opmerking": MERK}).insert()
			stand.maak_journaalpost()
			aantal += 1
	return aantal


def _btw_aangiftes(bedrijf, jaren, vandaag) -> int:
	"""Per kwartaal een Btw-aangifte (concept, met de conceptfacturen meegeteld), de journaalpost die de btw-rekeningen
	leegboekt naar Btw-afdracht, en de betaling aan de Belastingdienst als bankregel."""
	aantal = 0
	for jaar in jaren:
		for kwartaal in range(1, 5):
			van = datetime.date(jaar, 3 * kwartaal - 2, 1)
			tot = datetime.date(jaar + (kwartaal == 4), (3 * kwartaal) % 12 + 1, 1) - datetime.timedelta(days=1)
			if tot >= vandaag or frappe.db.exists("Btw-aangifte", {"bedrijf": bedrijf.name, "van": _datum(van), "docstatus": ("<", 2)}):
				continue
			aangifte = frappe.get_doc(
				{"doctype": "Btw-aangifte", "bedrijf": bedrijf.name, "tijdvak": "Kwartaal", "van": _datum(van), "tot": _datum(tot), "concepten_meetellen": 1, "opmerking": MERK}
			).insert()
			aangifte.maak_journaalpost()
			betaald = tot + datetime.timedelta(days=29)
			if betaald <= vandaag and flt(aangifte.te_betalen):
				_bank(bedrijf, bedrijf.bank, _datum(betaald), aangifte.te_betalen < 0, abs(aangifte.te_betalen), f"Omzetbelasting {jaar} kwartaal {kwartaal} {aangifte.name}", "Belastingdienst")
			aantal += 1
	return aantal


def wizard() -> bool:
	"""Op een verse site: rondt de wizard van ERPNext af met de holding als eerste bedrijf (Nederland, euro), zodat de
	stamgegevens van ERPNext er staan. Op een site die al is ingericht gebeurt er niets."""
	if frappe.is_setup_complete():
		return False
	from frappe.desk.page.setup_wizard.setup_wizard import initialize_system_settings_and_user, setup_complete

	jaar = getdate(today()).year
	initialize_system_settings_and_user({"language": "nl", "country": "Netherlands", "currency": "EUR", "time_zone": "Europe/Amsterdam"}, {})
	setup_complete(
		{
			"language": frappe.db.get_value("Language", "nl", "language_name") or "Nederlands",
			"lang": "nl",
			"country": "Netherlands",
			"timezone": "Europe/Amsterdam",
			"currency": "EUR",
			"company_name": BEDRIJVEN[0]["naam"],
			"company_abbr": BEDRIJVEN[0]["afkorting"],
			"chart_of_accounts": "Standard",
			"fy_start_date": f"{jaar}-01-01",
			"fy_end_date": f"{jaar}-12-31",
			"setup_demo": 0,
		}
	)
	frappe.db.commit()
	frappe.clear_cache()
	if not frappe.is_setup_complete():
		frappe.throw("De wizard van ERPNext is niet afgerond.")
	return True


def maak(zaad: int = 2026, jaren: str | list | None = None, alleen: str | None = None) -> dict:
	"""Maakt het demonstratiebedrijf, alles als concept. Geeft per bedrijf terug wat er is aangemaakt.
	Met `alleen` (bijvoorbeeld "hout bouw") krijgen alleen die bedrijven hun administratie; de groep zelf, de
	relaties en het fundament komen er altijd."""
	frappe.only_for("System Manager")
	if isinstance(jaren, str):
		jaren = [int(j) for j in jaren.replace(",", " ").split()]
	vandaag = getdate(today())
	jaren = list(jaren or [vandaag.year - 2, vandaag.year - 1, vandaag.year])
	rng = random.Random(int(zaad))
	wizard()
	boekhouding.zorg_voor_velden()
	_boekjaren(jaren)
	bedrijven = _bedrijven(rng)
	fundament = _fundament(rng, bedrijven, jaren[0])
	frappe.db.commit()
	mensen = _mensen(rng, bedrijven)
	_hierarchie(bedrijven)
	klanten, leveranciers = _relaties(rng)
	frappe.db.commit()
	uit = {"fundament": fundament}
	kies = set((alleen or "").replace(",", " ").split())
	if not kies:
		uit["beheervergoedingen"] = _beheervergoeding(bedrijven, jaren, vandaag)
		frappe.db.commit()
	for sleutel, bedrijf in bedrijven.items():
		# Per bedrijf een eigen reeks: een bedrijf opnieuw of later maken verandert de andere niet.
		if kies and sleutel not in kies:
			continue
		eigen = random.Random(f"{zaad}-{sleutel}")
		if frappe.db.exists("Journal Entry", {"company": bedrijf.name, "user_remark": ("like", f"Loonjournaalpost%{MERK}%")}):
			uit[sleutel] = "bestond al"
			continue
		tel = {"medewerkers": len(mensen[sleutel])}
		if sleutel != "holding":
			# Alleen de jaren waarvoor dit bedrijf cijfers heeft.
			eigen_jaren = [j for j in jaren if j in bedrijf["jaren"]]
			if sleutel == "hout":
				from openaec_bouw import demo_voorraad

				tel.update(demo_voorraad.maak(eigen, bedrijf, klanten, leveranciers, eigen_jaren, vandaag))
			else:
				tel.update(_projecten(eigen, bedrijf, klanten, leveranciers, mensen[sleutel], eigen_jaren, vandaag))
			if sleutel in ("bouw", "installatie"):
				tel["onderhanden_werk"] = _onderhanden_werk(bedrijf, eigen_jaren, vandaag)
		vast = _vaste_lasten(eigen, bedrijf, leveranciers, jaren, vandaag)
		tel["inkoop"] = tel.get("inkoop", 0) + vast["inkoop"]
		tel["bank"] = tel.get("bank", 0) + vast["bank"]
		tel["lonen"] = vast["lonen"]
		tel["btw_aangiftes"] = _btw_aangiftes(bedrijf, jaren, vandaag)
		frappe.db.commit()
		uit[sleutel] = tel
	return uit


def stand() -> dict:
	"""Wat er per bedrijf van de groep staat: aantallen, en omzet en directe kosten per jaar uit de (concept)facturen."""
	uit = {}
	for b in BEDRIJVEN:
		if not frappe.db.exists("Company", b["naam"]):
			continue
		per_jaar = {}
		for doctype, sleutel in (("Sales Invoice", "omzet"), ("Purchase Invoice", "inkoop")):
			# Inkoop die de voorraad in gaat, is geen kosten: de kostprijs van wat verkocht is komt hieronder.
			geen_voorraad = " and ifnull(update_stock, 0) = 0" if doctype == "Purchase Invoice" else ""
			for rij in frappe.db.sql(f"select year(posting_date) as jaar, sum(base_net_total) as som, count(*) as aantal from `tab{doctype}` where company = %s and docstatus < 2{geen_voorraad} group by year(posting_date)", b["naam"], as_dict=True):
				per_jaar.setdefault(rij.jaar, {})[sleutel] = round(flt(rij.som))
				per_jaar[rij.jaar][f"{sleutel}_aantal"] = rij.aantal
		for rij in frappe.db.sql(
			"""select year(j.posting_date) as jaar, sum(a.debit) as som from `tabJournal Entry Account` a join `tabJournal Entry` j on j.name = a.parent
			join `tabAccount` r on r.name = a.account where j.company = %s and j.docstatus < 2 and r.account_number in ('4010', '4020', '4030') group by year(j.posting_date)""",
			b["naam"],
			as_dict=True,
		):
			per_jaar.setdefault(rij.jaar, {})["lonen"] = round(flt(rij.som))
		for rij in frappe.db.sql(
			"""select year(f.posting_date) as jaar, sum(r.stock_qty * a.valuation_rate) as som from `tabSales Invoice Item` r join `tabSales Invoice` f on f.name = r.parent
			join `tabItem` a on a.name = r.item_code where f.company = %s and f.docstatus < 2 and a.is_stock_item = 1 group by year(f.posting_date)""",
			b["naam"],
			as_dict=True,
		):
			per_jaar.setdefault(rij.jaar, {})["kostprijs_voorraad"] = round(flt(rij.som))
		# De afschrijving per jaar uit het register van vaste activa (lineair, per kwartaal).
		afschrijving = frappe.db.sql(
			"""select sum((a.net_purchase_amount - ifnull(f.expected_value_after_useful_life, 0)) / f.total_number_of_depreciations * 12 / f.frequency_of_depreciation)
			from `tabAsset` a join `tabAsset Finance Book` f on f.parent = a.name where a.company = %s and a.docstatus < 2""",
			b["naam"],
		)[0][0]
		for cijfers in per_jaar.values():
			cijfers["afschrijving"] = round(flt(afschrijving))
			cijfers["resultaat"] = cijfers.get("omzet", 0) - cijfers.get("inkoop", 0) - cijfers.get("lonen", 0) - cijfers.get("kostprijs_voorraad", 0) - cijfers["afschrijving"]
		uit[b["naam"]] = {
			"projecten": frappe.db.count("Project", {"company": b["naam"]}),
			"medewerkers": frappe.db.count("Employee", {"company": b["naam"]}),
			"banktransacties": frappe.db.count("Bank Transaction", {"company": b["naam"]}),
			"journaalposten": frappe.db.count("Journal Entry", {"company": b["naam"]}),
			"per_jaar": dict(sorted(per_jaar.items())),
		}
	return uit


def portretten(pad: str | None = None) -> list[dict]:
	"""Per medewerker van de groep een opdracht voor een beeldgenerator (`demo_mensen.portretprompt`). Met `pad` komt
	de lijst ook als JSON-bestand op die plek. De foto's zelf worden hier niet gemaakt."""
	import json

	from openaec_bouw.demo_mensen import GEZICHTEN, portretprompt

	jaar, uit = getdate(today()).year, []
	for b in BEDRIJVEN:
		typering = {(g[0], g[1]): g[7] for g in GEZICHTEN.get(b["sleutel"], [])}
		for m in frappe.get_all("Employee", filters={"company": b["naam"]}, fields=["name", "first_name", "last_name", "gender", "date_of_birth", "designation"], order_by="name"):
			uit.append(
				{
					"medewerker": m.name,
					"naam": f"{m.first_name} {m.last_name}",
					"bedrijf": b["naam"],
					"functie": m.designation,
					"bestand": f"{frappe.scrub(m.first_name + ' ' + m.last_name)}-{m.name.lower()}.jpg",
					"opdracht": portretprompt(m.first_name, m.last_name, m.gender, getdate(m.date_of_birth).year, m.designation or "medewerker", b["sleutel"], jaar, typering.get((m.first_name, m.last_name), "")),
				}
			)
	if pad:
		with open(pad, "w", encoding="utf-8") as f:
			json.dump(uit, f, ensure_ascii=False, indent=1)
	return uit
