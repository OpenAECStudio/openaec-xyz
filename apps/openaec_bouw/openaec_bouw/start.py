"""Het startscherm: de tegel Bouwbedrijf."""

import frappe


def mag_zien() -> bool:
	"""De tegel is voor wie in het bureaublad werkt; een portaalgebruiker heeft er niets aan."""
	return frappe.session.user == "Administrator" or frappe.get_cached_value("User", frappe.session.user, "user_type") == "System User"
