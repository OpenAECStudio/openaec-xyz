// Onderhanden werk: de stand verversen en de journaalpost met de mutatie maken.
frappe.ui.form.on("Onderhanden Werk", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.peildatum) {
			// Standaard het einde van de vorige maand.
			frm.set_value("peildatum", frappe.datetime.add_days(frappe.datetime.month_start(), -1));
		}
	},
	refresh(frm) {
		if (frm.is_new()) return;
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Stand verversen"), () => frm.save());
		}
		if (frm.doc.docstatus < 2 && !frm.doc.journaalpost) {
			frm.add_custom_button(__("Journaalpost maken"), () =>
				frm.call("maak_journaalpost").then((r) => {
					if (r.message) {
						frappe.show_alert({ message: __("Journaalpost {0} staat klaar als concept", [r.message]), indicator: "green" });
						frm.reload_doc();
					} else {
						frappe.msgprint(__("Er is geen mutatie sinds de vorige stand."));
					}
				}),
			);
		}
	},
});
