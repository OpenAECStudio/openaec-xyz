// Btw-aangifte: het tijdvak invullen op het gekozen kwartaal, de cijfers verversen en de journaalpost maken.
frappe.ui.form.on("Btw-aangifte", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.van) {
			// Standaard het vorige kwartaal: dat is de aangifte die nu gedaan moet worden.
			const vorig = frappe.datetime.add_months(frappe.datetime.quarter_start(), -3);
			frm.set_value("van", vorig);
			frm.set_value("tot", frappe.datetime.add_days(frappe.datetime.add_months(vorig, 3), -1));
		}
	},
	refresh(frm) {
		if (frm.is_new()) return;
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Cijfers verversen"), () => frm.save());
		}
		if (frm.doc.docstatus < 2 && !frm.doc.journaalpost) {
			frm.add_custom_button(__("Journaalpost maken"), () =>
				frm.call("maak_journaalpost").then((r) => {
					if (r.message) {
						frappe.show_alert({ message: __("Journaalpost {0} staat klaar als concept", [r.message]), indicator: "green" });
						frm.reload_doc();
					} else {
						frappe.msgprint(__("Er is in dit tijdvak geen btw om te boeken."));
					}
				}),
			);
		}
	},
});
