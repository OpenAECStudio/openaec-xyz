// De klant uitnodigen: de SuperCloud stuurt een mail; hij logt in met zijn Apple-, Microsoft- of Google-account.
frappe.ui.form.on("Portaaltoegang", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.gebruiker) return;
		frm.add_custom_button(__("Uitnodigen"), () =>
			frappe
				.call({ method: "openaec_bouw.portaal.uitnodigen", args: { toegang_naam: frm.doc.name }, freeze: true })
				.then(() => frappe.show_alert({ message: __("Uitnodiging verstuurd naar {0}", [frm.doc.email]), indicator: "green" })),
		);
	},
});
