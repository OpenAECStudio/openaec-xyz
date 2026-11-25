"""Het demonstratiebedrijf, deel mensen: de vaste gezichten van de groep.

Per bedrijf een handvol mensen met een naam, een functie en een karakter. Zij komen terug in de post, op het intranet
en in de rapportages; de overige medewerkers krijgen een willekeurige naam. Alle personen zijn verzonnen.

`portretprompt` geeft per medewerker een opdracht voor een beeldgenerator, zodat iedereen een foto kan krijgen die
bij leeftijd, functie en bedrijf past. De foto's zelf worden hier niet gemaakt.
"""

# sleutel van het bedrijf → [(voornaam, achternaam, geslacht, geboortejaar, functie, afdeling, in dienst, typering)]
GEZICHTEN = {
	"holding": [
		("Willemijn", "Noorderkade", "Female", 1968, "Directeur", "Directie", 1996, "algemeen directeur en dochter van de oprichter; kalm, kent iedereen bij naam"),
		("Gerben", "Hofstede", "Male", 1972, "Financieel directeur", "Financiën", 2011, "financieel directeur; precies, stelt de lastige vragen over de kwartaalcijfers"),
		("Samira", "Benali", "Female", 1984, "Hoofd personeelszaken", "Personeelszaken", 2017, "hoofd personeelszaken; direct en betrokken"),
		("Jorrit", "van der Veen", "Male", 1990, "ICT-beheerder", "ICT", 2020, "beheert de systemen van de hele groep; droog gevoel voor humor"),
	],
	"bouw": [
		("Hendrik", "Oosterhuis", "Male", 1966, "Directeur", "Uitvoering", 1989, "directeur van het bouwbedrijf; begon als timmerman, zit liever op de bouw dan op kantoor"),
		("Marloes", "Dijkstra", "Female", 1981, "Projectleider", "Werkvoorbereiding", 2009, "projectleider nieuwbouw; houdt planning en opdrachtgever strak"),
		("Kees", "Brouwer", "Male", 1975, "Uitvoerder", "Uitvoering", 2001, "uitvoerder; praktisch, mailt kort en zonder hoofdletters"),
		("Fenna", "Postma", "Female", 1993, "Calculator", "Calculatie", 2018, "calculator; snel met cijfers, vergeet soms een stelpost"),
		("Ria", "Veenstra", "Female", 1970, "Administratie", "Administratie", 1998, "hoofd administratie; bewaakt de termijnen en de G-rekening"),
	],
	"installatie": [
		("Mehmet", "Yilmaz", "Male", 1976, "Directeur", "Projecten", 2004, "directeur van het installatiebedrijf; ondernemend, altijd onderweg"),
		("Lotte", "Wolters", "Female", 1988, "Vestigingsleider", "Projecten", 2014, "vestigingsleider Deventer; bouwt de vestiging uit"),
		("Arjan", "Koster", "Male", 1979, "Projectleider", "Projecten", 2007, "projectleider klimaatinstallaties; technisch sterk"),
		("Daan", "Nijland", "Male", 1996, "Monteur", "Service en onderhoud", 2016, "servicemonteur; lost storingen op en vergeet de werkbon in te vullen"),
		("Petra", "Kok", "Female", 1973, "Administratie", "Administratie", 2010, "administratie en planning van de servicedienst"),
	],
	"advies": [
		("Esther", "Schouten", "Female", 1974, "Directeur", "Projectleiding", 2003, "directeur van het adviesbureau; constructeur van huis uit"),
		("Thijs", "Mulder", "Male", 1986, "Constructeur", "Constructies", 2012, "senior constructeur; grondig, levert liever een dag later dan half"),
		("Naomi", "El Amrani", "Female", 1992, "Modelleur", "BIM en tekenwerk", 2019, "BIM-coördinator; verbindt ontwerp en uitvoering"),
		("Ruben", "Hoekstra", "Male", 1983, "Projectleider", "Bouwfysica", 2015, "adviseur bouwfysica en brandveiligheid"),
	],
	"sonderingen": [
		("Gerrit", "Kuipers", "Male", 1969, "Directeur", "Geotechnisch advies", 1999, "directeur van het sondeerbedrijf; geotechnicus, bezorgd over de stilstand van de wagen"),
		("Wout", "ten Brinke", "Male", 1987, "Sondeermeester", "Veldwerk", 2013, "sondeermeester; buiten in alle weersomstandigheden"),
		("Ilse", "Bos", "Female", 1991, "Constructeur", "Laboratorium", 2018, "geotechnisch adviseur en hoofd van het laboratorium"),
	],
	"hout": [
		("Pieter", "van Dijk", "Male", 1971, "Directeur", "Verkoop", 2000, "directeur van de houthandel; kent elke houtsoort en elke klant"),
		("Anouk", "de Groot", "Female", 1985, "Inkoper", "Inkoop", 2012, "inkoper tropisch hardhout; bewaakt de herkomst en de keurmerken"),
		("Bas", "Hendriks", "Male", 1994, "Verkoper", "Verkoop", 2019, "verkoper binnendienst; belooft soms een levertijd die niet haalbaar is"),
		("Henk", "Visser", "Male", 1964, "Magazijnmedewerker", "Magazijn en expeditie", 1992, "chef magazijn en zagerij; werkt er het langst van iedereen"),
	],
	"materieel": [
		("Stefan", "Dekker", "Male", 1978, "Directeur", "Verhuur", 2008, "directeur van de materieelverhuur; rekent in bezettingsgraad"),
		("Karin", "Peters", "Female", 1982, "Verkoper", "Verhuur", 2015, "planner verhuur; puzzelt met kranen en verreikers"),
		("Youssef", "Bakker", "Male", 1989, "Monteur", "Werkplaats en keuringen", 2017, "keurmeester; geen keuring, geen verhuur"),
	],
}

SETTING = {
	"holding": "in een licht kantoor met uitzicht op een haven",
	"bouw": "op een bouwplaats met een woningbouwproject op de achtergrond",
	"installatie": "in een technische ruimte met leidingwerk op de achtergrond",
	"advies": "in een ontwerpstudio met tekeningen en een beeldscherm op de achtergrond",
	"sonderingen": "buiten op een bouwterrein naast een sondeerwagen",
	"hout": "in een houtloods tussen gestapelde balken",
	"materieel": "op een werf met een torenkraan op de achtergrond",
}
KLEDING = {
	"Directeur": "nette maar informele kleding",
	"Financieel directeur": "een donker colbert zonder das",
	"Uitvoerder": "een werkjas en een witte bouwhelm in de hand",
	"Monteur": "een donkerblauwe werkjas",
	"Timmerman": "een werkbroek en een fleecevest",
	"Sondeermeester": "een oranje veiligheidsjas",
	"Magazijnmedewerker": "een bodywarmer en werkhandschoenen in de hand",
	"Chauffeur": "een bodywarmer",
}


def portretprompt(voornaam: str, achternaam: str, geslacht: str, geboortejaar: int, functie: str, sleutel: str, peiljaar: int, typering: str = "") -> str:
	"""Een opdracht voor een beeldgenerator: een portret dat bij deze verzonnen medewerker past."""
	leeftijd = peiljaar - geboortejaar
	wie = "vrouw" if geslacht == "Female" else "man"
	kleding = KLEDING.get(functie, "verzorgde, alledaagse werkkleding")
	karakter = f" Uitstraling: {typering.split(';')[-1].strip()}." if typering else ""
	return (
		f"Realistische portretfoto van een Nederlandse {wie} van ongeveer {leeftijd} jaar, {functie.lower()} bij een bouwbedrijf, "
		f"{SETTING.get(sleutel, 'op kantoor')}, in {kleding}. Hoofd en schouders, kijkt in de camera, natuurlijk daglicht, "
		f"zachte onscherpe achtergrond, vriendelijke en zakelijke uitdrukking.{karakter} "
		"Stijl: bedrijfsportret voor een intranet, vierkant formaat. Geen tekst, geen logo's, geen bestaande persoon."
	)
