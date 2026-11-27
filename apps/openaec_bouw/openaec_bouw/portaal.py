"""Klantenportaal: de klant volgt zijn project (voortgang, mijlpalen, foto's) en praat met het bedrijf.

Twee ingangen (zie `docs/klantenportaal.md`):

- **Verborgen link** `/portaal/l/<sleutel>`: alleen bekijken, geen account. Alleen de hash van de sleutel staat in
  de database (Portaallink); de link heeft een einddatum en kan ingetrokken worden.
- **Inloggen** (Apple, Microsoft of Google via de inlog van de SuperCloud): `/portaal` en `/portaal/p/<project>`.
  Toegang via Portaaltoegang op het e-mailadres; de klant is een Website User (gast), geen ERP-gebruiker.

Elke vraag gaat via `toegang()`, die per project nagaat of deze bezoeker het mag zien. Elke inzage en elk bericht
staat in het Portaallogboek.
"""

import hashlib
import secrets

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_url, getdate, now_datetime, today

GELDIG_DAGEN = 90
MAX_FOTOS = 60
MAX_BERICHTEN = 200

VELDEN = {
	"Task": [
		{
			"fieldname": "zichtbaar_voor_klant",
			"fieldtype": "Check",
			"label": "Zichtbaar voor de klant",
			"insert_after": "is_milestone",
			"description": "Deze taak staat als mijlpaal in het klantenportaal.",
		}
	],
}


def na_migratie():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(VELDEN, update=True)


# --- toegang ------------------------------------------------------------------------------------------------------


def _hash(sleutel: str) -> str:
	return hashlib.sha256(sleutel.encode()).hexdigest()


def link_bij(sleutel: str | None) -> frappe._dict | None:
	"""De geldige Portaallink bij deze sleutel, anders `None` (onbekend, verlopen of ingetrokken)."""
	if not sleutel or len(sleutel) < 20:
		return None
	link = frappe.db.get_value(
		"Portaallink",
		{"sleutel_hash": _hash(sleutel)},
		["name", "project", "geldig_tot", "ingetrokken"],
		as_dict=True,
	)
	if not link or link.ingetrokken or getdate(link.geldig_tot) < getdate(today()):
		return None
	return link


def is_bedrijf(gebruiker: str | None = None) -> bool:
	gebruiker = gebruiker or frappe.session.user
	return gebruiker != "Guest" and frappe.db.get_value("User", gebruiker, "user_type") == "System User"


def _toegang_klant(project: str, gebruiker: str) -> str | None:
	"""Naam van de actieve Portaaltoegang van deze gebruiker op dit project. Bij de eerste keer wordt de gebruiker
	op de toegang gezet (die is op e-mailadres aangemaakt)."""
	email = (frappe.db.get_value("User", gebruiker, "email") or gebruiker).lower()
	rij = frappe.db.get_value(
		"Portaaltoegang",
		{"project": project, "actief": 1, "email": email},
		["name", "gebruiker"],
		as_dict=True,
	) or frappe.db.get_value(
		"Portaaltoegang", {"project": project, "actief": 1, "gebruiker": gebruiker}, ["name", "gebruiker"], as_dict=True
	)
	if not rij:
		return None
	if rij.gebruiker != gebruiker:
		frappe.db.set_value("Portaaltoegang", rij.name, "gebruiker", gebruiker, update_modified=False)
	return rij.name


def toegang(project: str | None, sleutel: str | None = None) -> frappe._dict:
	"""Wie kijkt er naar dit project: `soort` is "bedrijf" (medewerker met leesrecht op het project, ziet wat de
	klant ziet), "klant" (ingelogd met Portaaltoegang) of "link" (verborgen link, alleen bekijken). Geen toegang:
	PermissionError, zonder te zeggen of het project bestaat."""
	gebruiker = frappe.session.user
	if sleutel:
		link = link_bij(sleutel)
		if link and (not project or link.project == project):
			return frappe._dict(soort="link", project=link.project, link=link.name, mag_schrijven=False)
	elif project and gebruiker != "Guest":
		if is_bedrijf(gebruiker) and frappe.has_permission("Project", "read", project):
			return frappe._dict(soort="bedrijf", project=project, link=None, mag_schrijven=True)
		if _toegang_klant(project, gebruiker):
			return frappe._dict(soort="klant", project=project, link=None, mag_schrijven=True)
	frappe.throw(_("Deze pagina bestaat niet of de link is verlopen."), frappe.PermissionError)


def mijn_projecten(gebruiker: str | None = None) -> list[frappe._dict]:
	"""De projecten waar deze (ingelogde) klant toegang toe heeft."""
	gebruiker = gebruiker or frappe.session.user
	if gebruiker == "Guest":
		return []
	email = (frappe.db.get_value("User", gebruiker, "email") or gebruiker).lower()
	namen = set(frappe.get_all("Portaaltoegang", filters={"actief": 1, "email": email}, pluck="project"))
	namen |= set(frappe.get_all("Portaaltoegang", filters={"actief": 1, "gebruiker": gebruiker}, pluck="project"))
	if not namen:
		return []
	return frappe.get_all(
		"Project",
		filters={"name": ["in", list(namen)]},
		fields=["name", "project_name", "status", "percent_complete", "expected_end_date", "company"],
		order_by="modified desc",
	)


def log(actie: str, project: str | None = None, link: str | None = None, details: str | None = None) -> None:
	frappe.get_doc(
		{
			"doctype": "Portaallogboek",
			"project": project,
			"actie": actie,
			"gebruiker": frappe.session.user,
			"link": link,
			"ip": getattr(frappe.local, "request_ip", None),
			"details": details,
		}
	).insert(ignore_permissions=True)


# --- wat de klant ziet --------------------------------------------------------------------------------------------


def gegevens(t: frappe._dict) -> frappe._dict:
	"""Alles wat de pagina van een project toont, voor deze bezoeker. Alleen wat gedeeld is; berichten alleen voor
	wie ingelogd is (niet via een link)."""
	p = frappe.db.get_value(
		"Project",
		t.project,
		["name", "project_name", "status", "percent_complete", "expected_start_date", "expected_end_date", "company"],
		as_dict=True,
	)
	bedrijf = frappe.db.get_value("Company", p.company, ["company_name", "company_logo"], as_dict=True) if p.company else None
	mijlpalen = frappe.get_all(
		"Task",
		filters={"project": t.project, "zichtbaar_voor_klant": 1},
		fields=["subject", "status", "exp_start_date", "exp_end_date", "progress"],
		order_by="exp_start_date asc, creation asc",
	)
	fotos = frappe.get_all(
		"Bouwfoto",
		filters={"project": t.project, "gedeeld": 1},
		fields=["name", "datum", "bijschrift"],
		order_by="datum desc, creation desc",
		limit=MAX_FOTOS,
	)
	for foto in fotos:
		foto.url = foto_url(foto.name, t)
	berichten = []
	if t.soort != "link":
		berichten = frappe.get_all(
			"Portaalbericht",
			filters={"project": t.project},
			fields=["van_naam", "van_klant", "tekst", "creation"],
			order_by="creation asc",
			limit=MAX_BERICHTEN,
		)
	return frappe._dict(project=p, bedrijf=bedrijf, mijlpalen=mijlpalen, fotos=fotos, berichten=berichten, toegang=t)


def foto_url(naam: str, t: frappe._dict) -> str:
	vraag = f"naam={naam}"
	if t.soort == "link":
		vraag += f"&sleutel={frappe.form_dict.get('sleutel') or ''}"
	return f"/api/method/openaec_bouw.portaal.foto?{vraag}"


@frappe.whitelist(allow_guest=True, methods=["GET"])
def foto(naam: str, sleutel: str | None = None):
	"""De foto zelf, ook als het bestand privé is: alleen als deze bezoeker het project mag zien en de foto gedeeld is."""
	rij = frappe.db.get_value("Bouwfoto", naam, ["project", "foto", "gedeeld"], as_dict=True)
	if not rij or not rij.gedeeld:
		raise frappe.PermissionError
	toegang(rij.project, sleutel)
	bestand = frappe.get_doc("File", {"file_url": rij.foto})
	frappe.local.response.filename = bestand.file_name
	frappe.local.response.filecontent = bestand.get_content()
	frappe.local.response.type = "download"
	frappe.local.response.display_content_as = "inline"


# --- berichten ----------------------------------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def bericht(project: str, tekst: str) -> dict:
	"""Een bericht in het gesprek van dit project, van de klant of van het bedrijf. Niet via een link."""
	t = toegang(project)
	tekst = (tekst or "").strip()
	if not tekst:
		frappe.throw(_("Het bericht is leeg."))
	if len(tekst) > 5000:
		frappe.throw(_("Het bericht is te lang."))
	doc = frappe.get_doc(
		{
			"doctype": "Portaalbericht",
			"project": project,
			"van": frappe.session.user,
			"van_klant": t.soort == "klant",
			"gelezen": t.soort == "bedrijf",
			"tekst": tekst,
		}
	).insert(ignore_permissions=True)
	log("bericht", project)
	if t.soort == "klant":
		_meld_bedrijf(doc)
	else:
		_meld_klanten(doc)
	return {"naam": doc.name}


def _meld_bedrijf(doc) -> None:
	"""Wie bij het project hoort (eigenaar en projectgebruikers die ERP-gebruiker zijn) krijgt een melding."""
	ontvangers = {frappe.db.get_value("Project", doc.project, "owner")}
	ontvangers |= set(frappe.get_all("Project User", filters={"parent": doc.project}, pluck="user"))
	for ontvanger in ontvangers:
		if ontvanger and is_bedrijf(ontvanger):
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"for_user": ontvanger,
					"type": "Alert",
					"document_type": "Portaalbericht",
					"document_name": doc.name,
					"subject": _("Bericht van de klant over {0}").format(doc.project),
					"email_content": frappe.utils.escape_html(doc.tekst[:500]),
				}
			).insert(ignore_permissions=True)


def _meld_klanten(doc) -> None:
	"""De klanten krijgen een mail dat er een nieuw bericht is, met een link naar het portaal; de tekst zelf staat
	alleen in het portaal."""
	adressen = frappe.get_all("Portaaltoegang", filters={"project": doc.project, "actief": 1}, pluck="email")
	if not adressen:
		return
	naam = frappe.db.get_value("Project", doc.project, "project_name") or doc.project
	url = get_url(f"/portaal/p/{doc.project}")
	frappe.sendmail(
		recipients=adressen,
		subject=_("Nieuw bericht over {0}").format(naam),
		message=_("Er staat een nieuw bericht voor u klaar over {0}.<br><br><a href=\"{1}\">Bekijk het in het portaal</a>").format(
			frappe.utils.escape_html(naam), url
		),
		reference_doctype="Project",
		reference_name=doc.project,
	)


# --- voor het bedrijf ---------------------------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def link_maken(project: str, omschrijving: str | None = None, dagen: int | None = None) -> dict:
	"""Een verborgen link om het project te bekijken. De sleutel is alleen nu te zien; bewaard wordt de hash."""
	frappe.has_permission("Project", "write", project, throw=True)
	sleutel = secrets.token_urlsafe(32)
	doc = frappe.get_doc(
		{
			"doctype": "Portaallink",
			"project": project,
			"omschrijving": omschrijving,
			"geldig_tot": add_days(today(), cint(dagen) or GELDIG_DAGEN),
			"sleutel_hash": _hash(sleutel),
		}
	).insert()
	log("link gemaakt", project, doc.name, omschrijving)
	return {"naam": doc.name, "url": get_url(f"/portaal/l/{sleutel}"), "geldig_tot": str(doc.geldig_tot)}


@frappe.whitelist(methods=["POST"])
def uitnodigen(toegang_naam: str) -> dict:
	"""Nodig de klant uit als gast van deze omgeving: hij krijgt van de SuperCloud een mail en logt daarna in met
	zijn Apple-, Microsoft- of Google-account. Een gast telt niet mee in het abonnement."""
	doc = frappe.get_doc("Portaaltoegang", toegang_naam)
	frappe.has_permission("Project", "write", doc.project, throw=True)
	if "openaec_beheer" not in frappe.get_installed_apps():
		frappe.throw(_("Uitnodigen kan alleen in een omgeving van de SuperCloud."))
	from openaec_beheer import api

	resultaat = api.nodig_uit(doc.email, "Gast", naam=doc.klant)
	log("uitgenodigd", doc.project, details=doc.email)
	return resultaat or {}


def bezocht(t: frappe._dict) -> None:
	"""Inzage loggen; via een link ook de teller op de link. Een paginaverzoek is een GET: zelf vastleggen."""
	if t.link:
		frappe.db.sql(
			"update `tabPortaallink` set bezoeken = ifnull(bezoeken, 0) + 1, laatst_bezocht = %s where name = %s",
			(now_datetime(), t.link),
		)
	log(f"bekeken ({t.soort})", t.project, t.link)
	frappe.db.commit()
