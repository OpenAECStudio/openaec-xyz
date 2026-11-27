"""/portaal/l/<sleutel> (verborgen link, alleen bekijken) en /portaal/p/<project> (ingelogd)."""

import frappe
from frappe import _

from openaec_bouw import portaal

no_cache = 1


def get_context(context):
	sleutel = frappe.form_dict.get("sleutel")
	project = frappe.form_dict.get("project")
	if not sleutel and frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = f"/login?redirect-to=/portaal/p/{project or ''}"
		raise frappe.Redirect
	try:
		t = portaal.toegang(project, sleutel)
	except frappe.PermissionError:
		frappe.local.response["http_status_code"] = 404
		context.geen_toegang = True
		context.title = _("Niet gevonden")
		return context
	portaal.bezocht(t)
	context.update(portaal.gegevens(t))
	context.no_breadcrumbs = True
	context.title = context.project.project_name or context.project.name
	context.sleutel = sleutel
	context.inloggen_url = f"/login?redirect-to=/portaal/l/{sleutel}" if sleutel else None
	context.ingelogd = frappe.session.user != "Guest"
	return context
