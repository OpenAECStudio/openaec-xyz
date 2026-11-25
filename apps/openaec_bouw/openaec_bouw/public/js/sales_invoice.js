// Op een geboekte verkoopfactuur: de factuur als UBL (NLCIUS) downloaden.
frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;
		frm.add_custom_button(
			__("UBL downloaden"),
			() => window.open(`/api/method/openaec_bouw.ubl.download?${new URLSearchParams({ factuur: frm.doc.name })}`),
			__("Nederland"),
		);
	},
});
