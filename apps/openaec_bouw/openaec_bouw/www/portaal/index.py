"""/portaal: de projecten van de ingelogde klant."""

import frappe
from frappe import _

from openaec_bouw import portaal

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/portaal"
		raise frappe.Redirect
	context.no_breadcrumbs = True
	context.title = _("Mijn projecten")
	context.projecten = portaal.mijn_projecten()
	context.is_bedrijf = portaal.is_bedrijf()
	return context
